# backend/main.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from pathlib import Path
import os, zipfile, uuid, traceback, logging, tempfile, shutil

# внутренние модули (важно запускать uvicorn как пакет: python -m uvicorn backend.main:app ...)
from .audio_processor import analyze_audio, normalize_audio
from .report_generator import generate_pdf_report
from .tags_editor import extract_tags, update_tags
from .presets import PRESETS
from .loudness_plot import plot_loudness_over_time
from .models import ProcessingHistory
from .db import init_db, SessionLocal

log = logging.getLogger("uvicorn.error")

# -------------------- Helpers: безопасный парсинг LUFS и строк --------------------
def _clean_number_str(raw: Optional[str]) -> str:
    """
    Нормализует строку числа:
    - красивые минусы (−/–/—) → обычный '-'
    - запятая → точка
    - убирает пробелы (включая NBSP)
    - оставляет только один минус в начале и одну точку
    """
    s = (raw or "").strip()
    # минусы
    s = (s.replace("\u2212", "-")   # −
           .replace("\u2013", "-")  # –
           .replace("\u2014", "-")) # —
    # запятая → точка, убрать пробелы
    s = (s.replace(",", ".")
           .replace("\u00A0", "")
           .replace(" ", ""))
    # один минус только в начале
    if s.count("-") > 1:
        s = "-" + s.replace("-", "")
    # одна точка
    if s.count(".") > 1:
        head, *tail = s.split(".")
        s = head + "." + "".join(tail)
    return s

def clean_lufs(raw: Optional[str]) -> float:
    s = _clean_number_str(raw)
    try:
        val = float(s)
    except Exception:
        raise ValueError("LUFS must be a number (e.g. -16, -14.5)")
    if not (-40.0 <= val <= 0.0):
        raise ValueError("LUFS must be between -40 and 0")
    return val

def choose_format(output_format: Optional[str], fmt: Optional[str], default_: str = "mp3") -> str:
    f = (output_format or fmt or default_ or "").strip().lower()
    if f not in {"wav", "mp3", "flac"}:
        raise ValueError("Invalid export format (expected wav/mp3/flac)")
    return f

# -------------------- Абсолютные пути --------------------
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
TEMP_DIR = BACKEND_DIR / "temp_files"      # для аплоадов и zip-ов
OUTPUT_DIR = BACKEND_DIR / "output"
PLOTS_DIR = OUTPUT_DIR / "plots"

for d in (TEMP_DIR, OUTPUT_DIR, PLOTS_DIR):
    d.mkdir(parents=True, exist_ok=True)

# Версия сервиса (можно прокинуть через ENV при деплое)
SERVICE_VERSION = os.getenv("LUFS_API_VERSION", "1.0.0")

app = FastAPI(title="Audio Loudness Normalizer & Tag Editor", version=SERVICE_VERSION)

# CORS (сузим при необходимости)
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

# ---------- Health/Ready ----------
@app.get("/health", include_in_schema=False)
def health():
    """Лёгкий health: только факт живости сервера."""
    return {"ok": True, "version": SERVICE_VERSION}

@app.head("/health", include_in_schema=False)
def health_head():
    # Для curl -I и внешних health-check'ов
    return Response(status_code=200)

@app.get("/ready", include_in_schema=False)
def ready():
    """
    Готовность: быстрая проверка БД и прав записи в TEMP_DIR.
    Ничего тяжёлого, без внешних сетевых вызовов.
    """
    checks = {"db": False, "temp_write": False}
    # DB
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        checks["db"] = True
    except Exception as e:
        log.error("[ready] db check failed: %s", e)

    # TEMP write
    try:
        test_file = TEMP_DIR / f".ready_{uuid.uuid4().hex}"
        test_file.write_text("ok", encoding="utf-8")
        if test_file.exists():
            test_file.unlink(missing_ok=True)
            checks["temp_write"] = True
    except Exception as e:
        log.error("[ready] temp write failed: %s", e)

    ok = all(checks.values())
    return JSONResponse(
        status_code=200 if ok else 503,
        content={"ok": ok, "checks": checks, "version": SERVICE_VERSION},
    )

@app.head("/ready", include_in_schema=False)
def ready_head():
    # Для curl -I и внешних readiness-check'ов
    return Response(status_code=200)

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

# FIX: опечатка (_DIR) ломала запуск
app.mount("/plots", StaticFiles(directory=PLOTS_DIR), name="plots")

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    fav = FRONTEND_DIR / "favicon.ico"
    if fav.exists():
        return FileResponse(fav)
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

# Принимаем оба пути (nginx может проксировать /lufs/api/* → /)
@app.post("/normalize")
@app.post("/normalize/")
async def normalize_audio_route(
    file: UploadFile = File(...),
    # принимаем строку, чтобы «красивые минусы» и запятые не ловили 422 у FastAPI/Pydantic
    target_lufs: str = Form("-14"),
    # совместимость: фронт может прислать output_format или fmt
    output_format: Optional[str] = Form(None),
    fmt: Optional[str] = Form(None),
    bitrate: str = Form("192k"),
    preset: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    # нормализуем preset
    if isinstance(preset, str) and preset.strip() == "":
        preset = None

    # проверка входного расширения
    in_ext = os.path.splitext(file.filename or "")[1].lower()
    if in_ext not in {".mp3", ".wav", ".flac"}:
        raise HTTPException(status_code=400, detail="Unsupported file format. Use MP3/WAV/FLAC.")

    # нормализуем формат экспорта
    try:
        out_fmt = choose_format(output_format, fmt, default_="mp3")
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    # парсим и валидируем target_lufs
    try:
        target = clean_lufs(target_lufs)
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=f"Invalid LUFS: {ve}")

    # сохраним аплоад во временный файл
    suffix = in_ext if in_ext else ".wav"
    with tempfile.NamedTemporaryFile(dir=TEMP_DIR, delete=False, suffix=suffix) as tmp_in:
        raw = await file.read()
        tmp_in.write(raw)
        temp_input = Path(tmp_in.name)

    _log("saved upload", path=str(temp_input), size=len(raw))

    try:
        # 1) анализ ДО нормализации (best-effort)
        lufs_before = peak = None
        try:
            lufs_before, peak = analyze_audio(str(temp_input))
            _log("analyzed_before", lufs_before=lufs_before, peak=peak)
        except Exception as e:
            _log("analyze_before_error", err=str(e))

        # 2) нормализация
        normalized_path = normalize_audio(
            input_path=str(temp_input),
            target_lufs=target,
            output_format=out_fmt,
            bitrate=bitrate,
            preset=preset,
        )
        _log("normalized", output=normalized_path, exists=os.path.exists(normalized_path))

        if not os.path.exists(normalized_path):
            raise RuntimeError("Normalization finished without output file")

        # 3) анализ ПОСЛЕ нормализации (best-effort)
        lufs_after = None
        try:
            lufs_after, _ = analyze_audio(normalized_path)
            _log("analyzed_after", lufs_after=lufs_after)
        except Exception as e:
            _log("analyze_after_error", err=str(e))

        # фактическая цель LUFS, учитывая пресет
        actual_target_lufs = (
            PRESETS[preset.lower()]
            if (preset and preset.lower() in PRESETS and (target is None or target == 0.0))
            else (target if target is not None else -14.0)
        )

        # 4) график (best-effort)
        plot_path = None
        try:
            plot_path = plot_loudness_over_time(normalized_path)  # путь к PNG
        except Exception as e:
            _log("plot_error", err=str(e))

        # 5) теги (best-effort)
        tags = {}
        try:
            if out_fmt == "mp3":
                tags = extract_tags(normalized_path)
            elif in_ext == ".mp3":
                tags = extract_tags(str(temp_input))
        except Exception as e:
            _log("tags_error", err=str(e))

        # 6) PDF-отчёт
        report_path = generate_pdf_report(
            filename=file.filename,
            lufs_before=lufs_before,
            lufs_after=lufs_after,
            peak=peak,
            target_lufs=actual_target_lufs,
            plot_path=plot_path,
            tags=tags,
        )

        # 7) История в БД (best-effort)
        try:
            db.add(ProcessingHistory(
                filename=file.filename,
                format=out_fmt,
                lufs_before=lufs_before,
                lufs_after=lufs_after,
                peak=peak,
                target_lufs=actual_target_lufs,
                plot_path=os.path.basename(plot_path) if plot_path else None,
            ))
            db.commit()
        except Exception as e:
            _log("history_db_error", err=str(e))

        # 8) ZIP-результат
        zip_filename = TEMP_DIR / f"result_{uuid.uuid4().hex}.zip"
        with zipfile.ZipFile(zip_filename, "w") as zipf:
            zipf.write(normalized_path, arcname=f"normalized.{out_fmt}")
            if report_path and os.path.exists(report_path):
                zipf.write(report_path, arcname="report.pdf")
            if plot_path and os.path.exists(plot_path):
                zipf.write(plot_path, arcname="loudness_plot.png")

        return FileResponse(str(zip_filename), filename="result.zip", media_type="application/x-zip-compressed")

    except HTTPException:
        raise
    except Exception as e:
        _log("normalize_route_error", err=str(e))
        return JSONResponse(status_code=400, content={"ok": False, "error": str(e)})

    finally:
        # подчистим загруженный временный файл
        try:
            if 'temp_input' in locals() and temp_input and temp_input.exists():
                temp_input.unlink(missing_ok=True)
        except Exception:
            pass


@app.post("/normalize_cached/")
async def normalize_cached_route(
    filename: str = Form(...),
    # совместимость: может прийти как число/строка/None
    target_lufs: Optional[str] = Form(None),
    # совместимость имён полей
    output_format: Optional[str] = Form(None),
    fmt: Optional[str] = Form(None),
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

    # формат экспорта
    try:
        out_fmt = choose_format(output_format, fmt, default_="wav")
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    # цель LUFS (может быть None → возьмём из пресета/дефолта)
    parsed_target: Optional[float] = None
    if target_lufs not in (None, "", "null"):
        try:
            parsed_target = clean_lufs(target_lufs)
        except ValueError as ve:
            raise HTTPException(status_code=422, detail=f"Invalid LUFS: {ve}")

    # анализ до нормализации
    lufs_before, peak = analyze_audio(str(temp_input))

    normalized_path = normalize_audio(
        input_path=str(temp_input),
        target_lufs=parsed_target if parsed_target is not None else None,
        output_format=out_fmt,
        bitrate=bitrate,
        preset=preset,
    )

    lufs_after, _ = analyze_audio(normalized_path)

    actual_target_lufs = (
        PRESETS[preset.lower()]
        if (preset and preset.lower() in PRESETS and (parsed_target is None or parsed_target == 0.0))
        else (parsed_target if parsed_target is not None else -14.0)
    )

    plot_path = None
    try:
        plot_path = plot_loudness_over_time(normalized_path)
    except Exception as e:
        _log("plot_error_cached", err=str(e))

    tags = {}
    try:
        if out_fmt == "mp3":
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
                format=out_fmt,
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
        zipf.write(normalized_path, arcname=f"normalized.{out_fmt}")
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
