# backend/audio_processor.py

from typing import Optional
from pathlib import Path
import uuid
import os
import ffmpeg
import soundfile as sf
import numpy as np
import pyloudnorm as pyln

from .presets import PRESETS


# === Папки для временных/выходных файлов (абсолютные пути) ===
BASE_DIR = Path(__file__).resolve().parent
RUNTIME_DIR = BASE_DIR / "runtime"
TMP_DIR = RUNTIME_DIR / "tmp"
OUT_DIR = RUNTIME_DIR / "out"
for _d in (TMP_DIR, OUT_DIR):
    _d.mkdir(parents=True, exist_ok=True)


def _tmpfile(suffix: str) -> str:
    """Абсолютный путь для временного файла с заданным суффиксом."""
    return str(TMP_DIR / f"{uuid.uuid4().hex}{suffix}")


def _decode_ffmpeg_error(e: Exception) -> str:
    """Достать читаемый stderr из исключения ffmpeg-python."""
    try:
        # ffmpeg.Error имеет атрибут stderr (bytes)
        stderr = getattr(e, "stderr", None)
        if stderr:
            return stderr.decode("utf-8", "ignore")
    except Exception:
        pass
    return str(e)


def _to_float32_pcm(data: np.ndarray) -> np.ndarray:
    """Привести произвольный аудиомассив к float32 в диапазоне [-1, 1]."""
    if data.dtype == np.float32:
        return data
    if np.issubdtype(data.dtype, np.floating):
        return data.astype(np.float32, copy=False)
    # int PCM -> float [-1, 1]
    iinfo = np.iinfo(data.dtype) if np.issubdtype(data.dtype, np.integer) else None
    if iinfo:
        return (data.astype(np.float32) / max(abs(iinfo.min), iinfo.max))
    # fallback
    return data.astype(np.float32)


# =======================================================================
# Анализ аудио
# =======================================================================
def analyze_audio(path: str):
    """
    Прогон через ffmpeg в эталонный WAV (stereo, 44.1k, s16), затем
    измерение интегральной громкости (LUFS) и пика.
    Возвращает (loudness_lufs: float, true_peak: float).
    """
    temp_wav = _tmpfile(".wav")
    try:
        (
            ffmpeg
            .input(path)
            .output(
                temp_wav,
                ac=2,           # stereo
                ar=44100,       # 44.1k
                sample_fmt="s16"  # 16-bit PCM
            )
            .overwrite_output()
            .run(quiet=True)
        )
    except Exception as e:
        raise Exception(f"FFmpeg failed (analyze stage): {_decode_ffmpeg_error(e)}")

    try:
        data, rate = sf.read(temp_wav, always_2d=True)  # shape: (samples, channels)
        data = _to_float32_pcm(data)
        # pyloudnorm ожидает (samples, channels) либо (samples,) — у нас (N, 2)
        meter = pyln.Meter(rate)
        loudness = meter.integrated_loudness(data)
        peak = float(np.max(np.abs(data)))
        return round(float(loudness), 2), round(peak, 4)
    except Exception as e:
        raise Exception(f"Analyze failed: {e}")
    finally:
        try:
            os.remove(temp_wav)
        except Exception:
            pass


# =======================================================================
# Нормализация аудио
# =======================================================================
def normalize_audio(
    input_path: str,
    target_lufs: Optional[float] = -14.0,
    output_format: str = "wav",
    bitrate: str = "192k",
    preset: Optional[str] = None
) -> str:
    """
    Нормализует аудио под target_lufs через ffmpeg loudnorm и сохраняет
    результат в runtime/out/*.ext. Возвращает абсолютный путь к файлу.
    Поддержка форматов: wav, mp3, flac.
    Примечание: у libmp3lame НЕТ параметра -preset — не передаём его.
    """

    # 1) Подтянуть из пресета, если target пустой
    if (target_lufs is None or target_lufs == 0.0) and preset:
        key = preset.strip().lower()
        if key in PRESETS:
            target_lufs = PRESETS[key]

    # 2) Валидация и «безопасное» значение по умолчанию
    if target_lufs is None or target_lufs == 0.0 or target_lufs < -70 or target_lufs > -5:
        target_lufs = -14.0

    ext = (output_format or "wav").lower()
    if ext not in ("wav", "mp3", "flac"):
        raise Exception(f"Unsupported output format: {ext}")

    # приведение битрейта к виду "<number>k" для mp3
    if ext == "mp3":
        b = (bitrate or "192k").strip().lower()
        if b.isdigit():
            bitrate = f"{b}k"
        elif not b.endswith("k"):
            # если пользователь передал "192" или "192000", нормализуем
            try:
                val = int(b)
                # если это похоже на 192000 — преобразуем в k
                bitrate = f"{val // 1000}k" if val > 1000 else f"{val}k"
            except Exception:
                bitrate = "192k"
        else:
            bitrate = b
    # путь вывода — абсолютный, в runtime/out
    output_path = str(OUT_DIR / f"normalized_{uuid.uuid4().hex}.{ext}")

    # Фильтр loudnorm: I=целевой LUFS, TP=-1dBFS, LRA=11дБ (стандартные)
    filters = f"loudnorm=I={target_lufs}:TP=-1.0:LRA=11"

    try:
        base_stream = ffmpeg.input(input_path)

        if ext == "wav":
            stream = base_stream.output(
                output_path,
                af=filters,
                ar=44100,
                ac=2,
                sample_fmt="s16"
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
        else:  # flac
            stream = base_stream.output(
                output_path,
                af=filters,
                ar=44100,
                ac=2,
                acodec="flac"
            )

        (
            stream
            .overwrite_output()
            .run(quiet=True)
        )

    except Exception as e:
        raise Exception(f"Normalization failed: {_decode_ffmpeg_error(e)}")

    if not os.path.exists(output_path):
        raise Exception("Normalization finished without output file")

    return output_path
