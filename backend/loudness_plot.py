# backend/loudness_plot.py
from pathlib import Path
import uuid
import numpy as np
import librosa
import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt

BACKEND_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BACKEND_DIR / "output"
PLOTS_DIR = OUTPUT_DIR / "plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)


def plot_loudness_over_time(audio_path: str) -> str:
    """
    Строит простой график огибающей RMS и сохраняет PNG в backend/output/plots.
    Возвращает абсолютный путь к PNG.
    """
    y, sr = librosa.load(audio_path, sr=44100, mono=True)
    # RMS в окне 2048, hop 512
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512).flatten()
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=512)

    out_png = PLOTS_DIR / f"loudness_{uuid.uuid4().hex}.png"

    plt.figure(figsize=(10, 3))
    plt.plot(times, rms)
    plt.title("RMS (proxy for loudness) over time")
    plt.xlabel("Time (s)")
    plt.ylabel("RMS")
    plt.tight_layout()
    plt.savefig(str(out_png), dpi=150)
    plt.close()

    return str(out_png)
