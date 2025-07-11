import pyloudnorm as pyln
import ffmpeg
import soundfile as sf
import os
import uuid
import numpy as np
from presets import PRESETS


def analyze_audio(path: str):
    temp_wav = f"temp_files/{uuid.uuid4().hex}.wav"
    try:
        ffmpeg.input(path).output(temp_wav, ac=2, ar=44100).overwrite_output().run(quiet=True)
    except ffmpeg.Error as e:
        raise Exception(f"FFmpeg failed: {e.stderr.decode()}")

    data, rate = sf.read(temp_wav)
    meter = pyln.Meter(rate)
    loudness = meter.integrated_loudness(data)
    peak = np.max(np.abs(data))
    os.remove(temp_wav)

    return round(loudness, 2), round(peak, 2)


def normalize_audio(input_path: str, target_lufs: float = -14.0, output_format: str = "wav", bitrate: str = "192k", preset: str = None) -> str:
    # 1. Применяем preset, если задан и target_lufs пустой или 0.0
    if (target_lufs is None or target_lufs == 0.0) and preset and preset.lower() in PRESETS:
        target_lufs = PRESETS[preset.lower()]

    # 2. Защита от невалидных значений LUFS
    if target_lufs is None or target_lufs == 0.0 or target_lufs < -70 or target_lufs > -5:
        target_lufs = -14.0  # безопасное значение по умолчанию

    ext = output_format.lower()
    output_path = f"temp_files/normalized_{uuid.uuid4().hex}.{ext}"

    try:
        base_stream = ffmpeg.input(input_path)
        filters = f"loudnorm=I={target_lufs}:TP=-1.0:LRA=11"

        if ext == "wav":
            stream = base_stream.output(
                output_path,
                af=filters,
                ar=44100,
                ac=2
            )
        elif ext == "mp3":
            stream = base_stream.output(
                output_path,
                af=filters,
                ar=44100,
                ac=2,
                audio_bitrate=bitrate,
                acodec="libmp3lame"
            )
        elif ext == "flac":
            stream = base_stream.output(
                output_path,
                af=filters,
                ar=44100,
                ac=2,
                acodec="flac"
            )
        else:
            raise Exception(f"Unsupported output format: {ext}")

        stream = stream.overwrite_output()
        stream.run(quiet=True)

    except ffmpeg.Error as e:
        raise Exception(f"Normalization failed: {e.stderr.decode()}")

    return output_path
