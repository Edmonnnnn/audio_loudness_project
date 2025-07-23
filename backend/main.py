from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import Optional
import os, io, zipfile, uuid

from audio_processor import analyze_audio, normalize_audio
from report_generator import generate_pdf_report
from tags_editor import extract_tags, update_tags
from presets import PRESETS
from loudness_plot import plot_loudness_over_time
from models import ProcessingHistory
from db import init_db, SessionLocal

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

@app.get("/")
def serve_index():
    return FileResponse("../frontend/index.html")

app.mount("/assets", StaticFiles(directory="../frontend/assets"), name="assets")
app.mount("/plots", StaticFiles(directory="output/plots"), name="plots")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/normalize/")
async def normalize_audio_route(
    file: UploadFile = File(...),
    target_lufs: Optional[float] = Form(None),
    output_format: str = Form("wav"),
    bitrate: str = Form("192k"),
    preset: str = Form(None),
    db: Session = Depends(get_db)
):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".mp3", ".wav", ".flac"]:
        raise HTTPException(status_code=400, detail="Unsupported file format.")
    if output_format not in ["wav", "mp3", "flac"]:
        raise HTTPException(status_code=400, detail="Invalid export format.")

    temp_input = f"temp_files/{file.filename}"
    with open(temp_input, "wb") as buffer:
        buffer.write(await file.read())

    lufs_before, peak = analyze_audio(temp_input)

    normalized_path = normalize_audio(
        input_path=temp_input,
        target_lufs=target_lufs,
        output_format=output_format,
        bitrate=bitrate,
        preset=preset
    )

    lufs_after, _ = analyze_audio(normalized_path)

    actual_target_lufs = (
        PRESETS[preset.lower()] if (not target_lufs or target_lufs == 0.0) and preset and preset.lower() in PRESETS
        else (target_lufs if target_lufs else -14.0)
    )

    plot_path = None
    try:
        plot_path = plot_loudness_over_time(normalized_path)
    except Exception as e:
        print(f"[WARN] Plot generation failed: {e}")
        
    
    # ✅ Читаем актуальные теги уже из НОВОГО ФАЙЛА!
    tags = {}
    if output_format == "mp3":
        tags = extract_tags(normalized_path)
    elif ext == ".mp3":
        tags = extract_tags(temp_input)

    report_path = generate_pdf_report(
        filename=file.filename,
        lufs_before=lufs_before,
        lufs_after=lufs_after,
        peak=peak,
        target_lufs=actual_target_lufs,
        plot_path=plot_path,
        tags=tags
    )

    db_record = ProcessingHistory(
        filename=file.filename,
        format=output_format,
        lufs_before=lufs_before,
        lufs_after=lufs_after,
        peak=peak,
        target_lufs=actual_target_lufs,
        plot_path=os.path.basename(plot_path) if plot_path else None
    )
    db.add(db_record)
    db.commit()

    # 📦 Сохраняем ZIP во временный файл (на диске)
    zip_filename = f"temp_files/result_{uuid.uuid4().hex}.zip"
    with zipfile.ZipFile(zip_filename, "w") as zipf:
        zipf.write(normalized_path, arcname=f"normalized.{output_format}")
        zipf.write(report_path, arcname="report.pdf")
        if plot_path and os.path.exists(plot_path):
            zipf.write(plot_path, arcname="loudness_plot.png")

    return FileResponse(
        path=zip_filename,
        filename="result.zip",
        media_type="application/x-zip-compressed"
    )

@app.post("/normalize_cached/")
async def normalize_cached_route(
    filename: str = Form(...),
    target_lufs: Optional[float] = Form(None),
    output_format: str = Form("wav"),
    bitrate: str = Form("192k"),
    preset: str = Form(None),
    db: Session = Depends(get_db)
):
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".mp3", ".wav", ".flac"]:
        raise HTTPException(status_code=400, detail="Unsupported file format.")

    temp_input = f"temp_files/{filename}"
    if not os.path.exists(temp_input):
        raise HTTPException(status_code=404, detail="File not found after tag edit!")

    lufs_before, peak = analyze_audio(temp_input)

    normalized_path = normalize_audio(
        input_path=temp_input,
        target_lufs=target_lufs,
        output_format=output_format,
        bitrate=bitrate,
        preset=preset
    )

    lufs_after, _ = analyze_audio(normalized_path)

    actual_target_lufs = (
        PRESETS[preset.lower()] if (not target_lufs or target_lufs == 0.0) and preset and preset.lower() in PRESETS
        else (target_lufs if target_lufs else -14.0)
    )

    plot_path = None
    try:
        plot_path = plot_loudness_over_time(normalized_path)
    except Exception as e:
        print(f"[WARN] Plot generation failed: {e}")

    tags = {}
    if output_format == "mp3":
        tags = extract_tags(normalized_path)
    elif ext == ".mp3":
        tags = extract_tags(temp_input)

    report_path = generate_pdf_report(
        filename=filename,
        lufs_before=lufs_before,
        lufs_after=lufs_after,
        peak=peak,
        target_lufs=actual_target_lufs,
        plot_path=plot_path,
        tags=tags
    )

    db_record = ProcessingHistory(
        filename=filename,
        format=output_format,
        lufs_before=lufs_before,
        lufs_after=lufs_after,
        peak=peak,
        target_lufs=actual_target_lufs,
        plot_path=os.path.basename(plot_path) if plot_path else None
    )
    db.add(db_record)
    db.commit()

    zip_filename = f"temp_files/result_{uuid.uuid4().hex}.zip"
    with zipfile.ZipFile(zip_filename, "w") as zipf:
        zipf.write(normalized_path, arcname=f"normalized.{output_format}")
        zipf.write(report_path, arcname="report.pdf")
        if plot_path and os.path.exists(plot_path):
            zipf.write(plot_path, arcname="loudness_plot.png")

    return FileResponse(
        path=zip_filename,
        filename="result.zip",
        media_type="application/x-zip-compressed"
    )

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
            "created_at": r.created_at.isoformat()
        }
        for r in records
    ]

@app.post("/tags/")
async def get_tags(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext != ".mp3":
        raise HTTPException(status_code=400, detail="Only MP3 files supported")
    temp_input = f"temp_files/{file.filename}"
    with open(temp_input, "wb") as buffer:
        buffer.write(await file.read())
    tags = extract_tags(temp_input)
    return tags

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
    cover: UploadFile = File(None)
):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext != ".mp3":
        raise HTTPException(status_code=400, detail="Only MP3 files supported")
    temp_input = f"temp_files/{file.filename}"
    with open(temp_input, "wb") as buffer:
        buffer.write(await file.read())
    cover_bytes = None
    cover_mime = None
    if cover:
        cover_bytes = await cover.read()
        cover_mime = cover.content_type
    update_tags(temp_input, {
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
        "tracknumber": tracknumber
    }, cover_bytes=cover_bytes, cover_mime=cover_mime)
    
    return {"message": "Tags updated successfully"}

