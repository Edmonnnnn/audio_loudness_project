# backend/report_generator.py
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader

import os
import uuid

# Абсолютные пути
BACKEND_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BACKEND_DIR / "output"
REPORTS_DIR = OUTPUT_DIR / "reports"
PLOTS_DIR = OUTPUT_DIR / "plots"

for d in (OUTPUT_DIR, REPORTS_DIR, PLOTS_DIR):
    d.mkdir(parents=True, exist_ok=True)


def _safe(val: Any) -> str:
    return "" if val is None else str(val)


def generate_pdf_report(
    filename: str,
    lufs_before: Optional[float],
    lufs_after: Optional[float],
    peak: Optional[float],
    target_lufs: Optional[float],
    plot_path: Optional[str],
    tags: Optional[Dict[str, str]] = None,
) -> str:
    """
    Генерирует PDF-отчёт и возвращает АБСОЛЮТНЫЙ путь к нему.
    Файл сохраняется в backend/output/reports/report_<uuid>.pdf
    """
    pdf_path = REPORTS_DIR / f"report_{uuid.uuid4().hex}.pdf"

    c = canvas.Canvas(str(pdf_path), pagesize=A4)
    width, height = A4

    y = height - 2 * cm

    c.setFont("Helvetica-Bold", 16)
    c.drawString(2 * cm, y, "Audio Loudness Report")
    y -= 1.2 * cm

    c.setFont("Helvetica", 10)
    c.drawString(2 * cm, y, f"Generated: {datetime.now().isoformat(timespec='seconds')}")
    y -= 0.8 * cm
    c.drawString(2 * cm, y, f"File: {_safe(filename)}")
    y -= 0.8 * cm

    # Параметры громкости
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2 * cm, y, "Loudness")
    y -= 0.8 * cm

    c.setFont("Helvetica", 11)
    c.drawString(2.5 * cm, y, f"Target LUFS: {_safe(target_lufs)}")
    y -= 0.6 * cm
    c.drawString(2.5 * cm, y, f"Measured Before: {_safe(lufs_before)} LUFS")
    y -= 0.6 * cm
    if lufs_after is not None:
        c.drawString(2.5 * cm, y, f"Measured After: {_safe(lufs_after)} LUFS")
        y -= 0.6 * cm
    c.drawString(2.5 * cm, y, f"Peak: {_safe(peak)}")
    y -= 1.0 * cm

    # Теги (если есть)
    if tags:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2 * cm, y, "Tags")
        y -= 0.8 * cm
        c.setFont("Helvetica", 10)
        for k, v in tags.items():
            text = f"{k}: {v}"
            # перенос по строкам, чтобы не уезжало за край
            max_width = width - 4 * cm
            while c.stringWidth(text, "Helvetica", 10) > max_width:
                # грубый перенос
                cut = int(len(text) * max_width / c.stringWidth(text, "Helvetica", 10)) - 3
                c.drawString(2.5 * cm, y, text[:cut] + "…")
                y -= 0.5 * cm
                text = text[cut:]
                if y < 4 * cm:
                    c.showPage()
                    y = height - 2 * cm
            c.drawString(2.5 * cm, y, text)
            y -= 0.5 * cm
            if y < 4 * cm:
                c.showPage()
                y = height - 2 * cm
        y -= 0.5 * cm

    # График, если есть
    if plot_path and os.path.exists(plot_path):
        try:
            img = ImageReader(plot_path)
            img_w, img_h = img.getSize()
            # впишем в ширину 16см и высоту 8см
            target_w = 16 * cm
            target_h = 8 * cm
            ratio = min(target_w / img_w, target_h / img_h)
            draw_w = img_w * ratio
            draw_h = img_h * ratio

            if y - draw_h < 2 * cm:
                c.showPage()
                y = height - 2 * cm

            c.setFont("Helvetica-Bold", 12)
            c.drawString(2 * cm, y, "Loudness Over Time")
            y -= 0.8 * cm

            c.drawImage(img, 2 * cm, y - draw_h, width=draw_w, height=draw_h, preserveAspectRatio=True, anchor='sw')
            y -= (draw_h + 0.8 * cm)
        except Exception:
            # если по какой-то причине картинку не удалось вставить — продолжаем без неё
            pass

    c.showPage()
    c.save()
    return str(pdf_path)
