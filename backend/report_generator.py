from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
import uuid
import os
from datetime import datetime

def generate_pdf_report(
    filename: str,
    lufs_before: float,
    lufs_after: float,
    peak: float,
    target_lufs,
    plot_path: str = None,
    tags: dict = None
) -> str:
    output_path = f"temp_files/report_{uuid.uuid4().hex}.pdf"
    c = canvas.Canvas(output_path, pagesize=A4)

    width, height = A4
    x = 2 * cm
    y = height - 2 * cm

    c.setFont("Helvetica-Bold", 16)
    c.drawString(x, y, "Audio Loudness Normalization Report")

    c.setFont("Helvetica", 12)
    y -= 2 * cm
    c.drawString(x, y, f"Original File: {filename}")

    y -= 1 * cm
    c.drawString(x, y, f"LUFS Before: {lufs_before}")
    y -= 1 * cm
    c.drawString(x, y, f"LUFS After:  {lufs_after}")
    y -= 1 * cm
    c.drawString(x, y, f"Peak Level:  {peak}")
    y -= 1 * cm
    c.drawString(x, y, f"Target LUFS: {target_lufs}")

    y -= 1 * cm
    c.drawString(x, y, f"Generated:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 🎵 Вставляем теги, если есть
    if tags:
        y -= 2 * cm
        c.setFont("Helvetica-Bold", 14)
        c.drawString(x, y, "Tags:")
        c.setFont("Helvetica", 12)
        for key, value in tags.items():
            if value:
                y -= 0.8 * cm
                c.drawString(x + 0.5 * cm, y, f"{key.capitalize()}: {value}")

    # 📈 Вставка графика
    if plot_path and os.path.exists(plot_path):
        try:
            y -= 2 * cm
            c.drawString(x, y, "Loudness Over Time:")
            y -= 12 * cm
            c.drawImage(plot_path, x, y, width=16 * cm, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"[WARN] Failed to insert plot: {e}")

    c.showPage()
    c.save()
    return output_path
