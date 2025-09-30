# backend/main.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import Optional
from pathlib import Path
import os, zipfile, uuid, traceback, logging, tempfile

# внутренние модули (важно запускать uvicorn как пакет: python -m uvicorn backend.main:app ...)
from .audio_processor import analyze_audio, normalize_audio
from .report_generator import generate_pdf_report
from .tags_editor import extract_tags, update_tags
from .presets import PRESETS
from .loudness_plot import plot_loudness_over_time
from .models import ProcessingHistory
from .db import init_db, SessionLocal

log = logging.getLogger("uvicorn.error")

# Абсолютные пути
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
TEMP_DIR = BACKEND_DIR / "temp_files"      # для аплоадов и zip-ов
OUTPUT_DIR = BACKEND_DIR / "output"
PLOTS_DIR = OUTPUT_DIR / "plots"

for d in (TEMP_DIR, OUTPUT_DIR, PLOTS_DIR):
    d.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Audio Loudness Normalizer & Tag Editor")

# CORS (для локалки можно сузить allow_origins при желании)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------- Глобальный обработчик исключений: читаемые ошибки вместо 500 ---------
@app.exception_handler(Exception)
async def all_exc_handler(request, exc):
    tb = traceback.format_exc()
    log.error("UNHANDLED: %s\n%s", exc, tb)
    # 400 — чтобы фронт мог прочитать тело
    return JSONResponse(status_code=400, content={"ok": False, "error": str(exc)})

# --------- Инициализация БД ---------
init_db()

# ---------- Раздача фронта/статики ----------
@app.get("/", include_in_schema=False)
def serve_index():
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=500, detail=f"index.html not found at {index_path}")
    return FileResponse(index_path)

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

ASSETS_DIR = FRONTEND_DIR / "assets"
if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")

app.mount("/plots", StaticFiles(directory=PLOTS_DIR), name="plots")

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    fav = FRONTEND_DIR / "favicon.ico"
    if fav.exists():
        return FileResponse(fav)
    from fastapi import Response
    return Response(status_code=204)

# ---------- DB Session ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- API ----------
def _log(msg, **kw):
    log.error("[normalize] %s %s", msg, kw if kw else "")

# Принимаем оба пути
@app.post("/normalize")
@app.post("/normalize/")
async def normalize_audio_route(
    file: UploadFile = File(...),
    target_lufs: float = Form(-14.0),
    fmt: str = Form("mp3"),            # поле формы от фронта
    bitrate: str = Form("192k"),
    preset: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    # нормализуем preset
    if isinstance(preset, str) and preset.strip() == "":
        preset = None

    # проверка входного расширения (не строго обязательно, но полезно)
    in_ext = os.path.splitext(file.filename or "")[1].lower()
    if in_ext not in {".mp3", ".wav", ".flac"}:
        raise HTTPException(status_code=400, detail="Unsupported file format. Use MP3/WAV/FLAC.")

    # нормализуем формат экспорта
    output_format = (fmt or "mp3").strip().lower()
    if output_format not in {"wav", "mp3", "flac"}:
        raise HTTPException(status_code=400, detail="Invalid export format (wav/mp3/flac).")

    # сохраним аплоад в уникальный TEMP-файл
    suffix = in_ext if in_ext else ".wav"
    with tempfile.NamedTemporaryFile(dir=TEMP_DIR, delete=False, suffix=suffix) as tmp_in:
        raw = await file.read()
        tmp_in.write(raw)
        temp_input = Path(tmp_in.name)

    _log("saved upload", path=str(temp_input), size=len(raw))

    try:
        # 1) анализ до нормализации (не критично, но полезно)
        try:
            lufs_before, peak = analyze_audio(str(temp_input))
            _log("analyzed_before", lufs_before=lufs_before, peak=peak)
        except Exception as e:
            _log("analyze_before_error", err=str(e))
            # продолжим всё равно

        # 2) нормализация (внутри audio_processor все временные — абсолютные и безопасные)
        normalized_path = normalize_audio(
            input_path=str(temp_input),
            target_lufs=target_lufs,
            output_format=output_format,
            bitrate=bitrate,
            preset=preset,
        )
        _log("normalized", output=normalized_path, exists=os.path.exists(normalized_path))

        if not os.path.exists(normalized_path):
            raise RuntimeError("Normalization finished without output file")

        # 3) анализ после нормализации (не критично, но красиво для отчёта)
        try:
            lufs_after, _ = analyze_audio(normalized_path)
            _log("analyzed_after", lufs_after=lufs_after)
        except Exception as e:
            _log("analyze_after_error", err=str(e))
            lufs_after = None

        # фактическая цель LUFS, учитывая пресет
        actual_target_lufs = (
            PRESETS[preset.lower()]
            if (not target_lufs or target_lufs == 0.0) and preset and preset.lower() in PRESETS
            else (target_lufs if target_lufs is not None else -14.0)
        )

        # 4) график (если упадёт — просто предупреждение)
        plot_path = None
        try:
            plot_path = plot_loudness_over_time(normalized_path)  # ожидается, что функция вернёт путь к PNG
        except Exception as e:
            _log("plot_error", err=str(e))

        # 5) теги (если итог MP3 — читаем из результата, иначе для отчёта можно взять из входного MP3)
        tags = {}
        try:
            if output_format == "mp3":
                tags = extract_tags(normalized_path)
            elif in_ext == ".mp3":
                tags = extract_tags(str(temp_input))
        except Exception as e:
            _log("tags_error", err=str(e))

        # 6) PDF-отчёт
        report_path = generate_pdf_report(
            filename=file.filename,
            lufs_before=lufs_before if 'lufs_before' in locals() else None,
            lufs_after=lufs_after,
            peak=peak if 'peak' in locals() else None,
            target_lufs=actual_target_lufs,
            plot_path=plot_path,
            tags=tags,
        )

        # 7) История в БД
        try:
            db.add(
                ProcessingHistory(
                    filename=file.filename,
                    format=output_format,
                    lufs_before=lufs_before if 'lufs_before' in locals() else None,
                    lufs_after=lufs_after,
                    peak=peak if 'peak' in locals() else None,
                    target_lufs=actual_target_lufs,
                    plot_path=os.path.basename(plot_path) if plot_path else None,
                )
            )
            db.commit()
        except Exception as e:
            _log("history_db_error", err=str(e))

        # 8) Упаковка ZIP и отдача
        zip_filename = TEMP_DIR / f"result_{uuid.uuid4().hex}.zip"
        with zipfile.ZipFile(zip_filename, "w") as zipf:
            zipf.write(normalized_path, arcname=f"normalized.{output_format}")
            if report_path and os.path.exists(report_path):
                zipf.write(report_path, arcname="report.pdf")
            if plot_path and os.path.exists(plot_path):
                zipf.write(plot_path, arcname="loudness_plot.png")

        return FileResponse(str(zip_filename), filename="result.zip", media_type="application/x-zip-compressed")

    except Exception as e:
        _log("normalize_route_error", err=str(e))
        return JSONResponse(status_code=400, content={"ok": False, "error": str(e)})

    finally:
        # подчистим загруженный временный файл
        try:
            if temp_input and temp_input.exists():
                temp_input.unlink()
        except Exception:
            pass


@app.post("/normalize_cached/")
async def normalize_cached_route(
    filename: str = Form(...),
    target_lufs: Optional[float] = Form(None),
    output_format: str = Form("wav"),
    bitrate: str = Form("192k"),
    preset: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    in_ext = os.path.splitext(filename)[1].lower()
    if in_ext not in {".mp3", ".wav", ".flac"}:
        raise HTTPException(status_code=400, detail="Unsupported file format.")

    temp_input = TEMP_DIR / filename
    if not temp_input.exists():
        raise HTTPException(status_code=404, detail="File not found after tag edit!")

    lufs_before, peak = analyze_audio(str(temp_input))

    normalized_path = normalize_audio(
        input_path=str(temp_input),
        target_lufs=target_lufs,
        output_format=output_format,
        bitrate=bitrate,
        preset=preset,
    )

    lufs_after, _ = analyze_audio(normalized_path)

    actual_target_lufs = (
        PRESETS[preset.lower()]
        if (not target_lufs or target_lufs == 0.0) and preset and preset.lower() in PRESETS
        else (target_lufs if target_lufs is not None else -14.0)
    )

    plot_path = None
    try:
        plot_path = plot_loudness_over_time(normalized_path)
    except Exception as e:
        _log("plot_error_cached", err=str(e))

    tags = {}
    try:
        if output_format == "mp3":
            tags = extract_tags(normalized_path)
        elif in_ext == ".mp3":
            tags = extract_tags(str(temp_input))
    except Exception as e:
        _log("tags_error_cached", err=str(e))

    report_path = generate_pdf_report(
        filename=filename,
        lufs_before=lufs_before,
        lufs_after=lufs_after,
        peak=peak,
        target_lufs=actual_target_lufs,
        plot_path=plot_path,
        tags=tags,
    )

    try:
        db.add(
            ProcessingHistory(
                filename=filename,
                format=output_format,
                lufs_before=lufs_before,
                lufs_after=lufs_after,
                peak=peak,
                target_lufs=actual_target_lufs,
                plot_path=os.path.basename(plot_path) if plot_path else None,
            )
        )
        db.commit()
    except Exception as e:
        _log("history_db_error_cached", err=str(e))

    zip_filename = TEMP_DIR / f"result_{uuid.uuid4().hex}.zip"
    with zipfile.ZipFile(zip_filename, "w") as zipf:
        zipf.write(normalized_path, arcname=f"normalized.{output_format}")
        if report_path and os.path.exists(report_path):
            zipf.write(report_path, arcname="report.pdf")
        if plot_path and os.path.exists(plot_path):
            zipf.write(plot_path, arcname="loudness_plot.png")

    return FileResponse(str(zip_filename), filename="result.zip", media_type="application/x-zip-compressed")


@app.get("/history/")
def get_history(db: Session = Depends(get_db)):
    records = db.query(ProcessingHistory).order_by(ProcessingHistory.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "filename": r.filename,
            "format": r.format,
            "lufs_before": r.lufs_before,
            "lufs_after": r.lufs_after,
            "peak": r.peak,
            "target_lufs": r.target_lufs,
            "plot_path": f"plots/{r.plot_path}" if r.plot_path else None,
            "created_at": r.created_at.isoformat(),
        }
        for r in records
    ]


@app.post("/tags/")
async def get_tags(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext != ".mp3":
        raise HTTPException(status_code=400, detail="Only MP3 files supported")
    temp_input = TEMP_DIR / file.filename
    with open(temp_input, "wb") as buffer:
        buffer.write(await file.read())
    return extract_tags(str(temp_input))


@app.post("/tags/save/")
async def save_tags(
    file: UploadFile = File(...),
    title: str = Form(""),
    artist: str = Form(""),
    album: str = Form(""),
    date: str = Form(""),
    genre: str = Form(""),
    composer: str = Form(""),
    discnumber: str = Form(""),
    comment: str = Form(""),
    albumartist: str = Form(""),
    publisher: str = Form(""),
    website: str = Form(""),
    tracknumber: str = Form(""),
    cover: UploadFile = File(None),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext != ".mp3":
        raise HTTPException(status_code=400, detail="Only MP3 files supported")

    temp_input = TEMP_DIR / file.filename
    with open(temp_input, "wb") as buffer:
        buffer.write(await file.read())

    cover_bytes = cover_mime = None
    if cover:
        cover_bytes = await cover.read()
        cover_mime = cover.content_type

    update_tags(
        str(temp_input),
        {
            "title": title,
            "artist": artist,
            "album": album,
            "date": date,
            "genre": genre,
            "composer": composer,
            "discnumber": discnumber,
            "comment": comment,
            "albumartist": albumartist,
            "publisher": publisher,
            "website": website,
            "tracknumber": tracknumber,
        },
        cover_bytes=cover_bytes,
        cover_mime=cover_mime,
    )
    return {"message": "Tags updated successfully"}
