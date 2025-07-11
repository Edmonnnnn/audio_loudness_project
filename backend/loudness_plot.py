import librosa
import numpy as np
import pyloudnorm as pyln
import matplotlib.pyplot as plt
import uuid
import os

def plot_loudness_over_time(file_path: str, frame_duration: float = 0.5) -> str:
    """
    Анализирует аудио и строит график LUFS по времени.
    Возвращает путь к PNG-файлу с графиком, сохранённым в output/plots/.
    """
    y, sr = librosa.load(file_path, sr=44100, mono=True)
    meter = pyln.Meter(sr)

    frame_len = int(frame_duration * sr)
    total_frames = len(y) // frame_len

    times = []
    loudness_values = []

    for i in range(total_frames):
        start = i * frame_len
        end = start + frame_len
        chunk = y[start:end]
        if len(chunk) == 0:
            continue
        lufs = meter.integrated_loudness(chunk)
        loudness_values.append(lufs)
        times.append(i * frame_duration)

    # Создаём папку, если нет
    os.makedirs("output/plots", exist_ok=True)

    # Уникальное имя
    plot_filename = f"loudness_plot_{uuid.uuid4().hex}.png"
    output_path = os.path.join("output", "plots", plot_filename)

    # Сохраняем
    plt.figure(figsize=(10, 4))
    plt.plot(times, loudness_values, label='LUFS')
    plt.xlabel("Time (s)")
    plt.ylabel("LUFS")
    plt.title("Loudness over Time")
    plt.grid(True)
    plt.ylim(-70, -5)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

    return output_path  # вернётся полный путь
