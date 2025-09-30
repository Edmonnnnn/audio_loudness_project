# backend/run_all.py
import os
import subprocess
import shutil
import psutil
import time
import webbrowser
from pathlib import Path

# Базовые пути
BASE_DIR = Path(__file__).resolve().parent           # .../backend
PROJECT_ROOT = BASE_DIR.parent                       # .../ (корень проекта)
TEMP_DIR = BASE_DIR / "temp_files"
PLOTS_DIR = BASE_DIR / "output" / "plots"
DB_FILE = TEMP_DIR / "history.db"

# Порты
BACKEND_PORT = 8111
FRONTEND_PORT = 3000

def kill_uvicorn_processes():
    print("[✖] Ищем процессы uvicorn...")
    count = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and any("uvicorn" in str(part) for part in cmdline):
                proc.kill()
                count += 1
        except Exception:
            continue
    if count:
        print(f"[✓] Завершено процессов: {count}")
    else:
        print("[✓] Uvicorn-процессов не найдено.")

def cleanup():
    print("[🌍] Чистим временные папки и БД...")
    try:
        if DB_FILE.exists():
            DB_FILE.unlink()
            print(f"[✓] Удалена БД: {DB_FILE}")
    except PermissionError:
        print("[!] Не удалось удалить history.db — занят другим процессом")

    shutil.rmtree(TEMP_DIR, ignore_errors=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[✓] Папка {TEMP_DIR} очищена")

    shutil.rmtree(PLOTS_DIR, ignore_errors=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[✓] Папка {PLOTS_DIR} очищена")

def run_backend():
    print(f"[🚀] Стартуем backend на {BACKEND_PORT}...")
    # Запускаем как пакет backend.main:app из КОРНЯ проекта
    subprocess.Popen(
        [
            "python", "-m", "uvicorn", "backend.main:app",
            "--reload", "--host", "127.0.0.1", "--port", str(BACKEND_PORT)
        ],
        cwd=PROJECT_ROOT,
        shell=False
    )

def run_frontend():
    print(f"[🌐] Стартуем http.server на http://127.0.0.1:{FRONTEND_PORT} ...")
    subprocess.Popen(
        ["python", "-m", "http.server", str(FRONTEND_PORT)],
        cwd=PROJECT_ROOT / "frontend",
        shell=False
    )
    time.sleep(1)
    webbrowser.open(f"http://127.0.0.1:{FRONTEND_PORT}")

if __name__ == "__main__":
    kill_uvicorn_processes()
    time.sleep(1)
    cleanup()
    run_backend()
    time.sleep(2)
    run_frontend()
    print(f"[✓] Готово! Frontend: http://127.0.0.1:{FRONTEND_PORT} | Backend: http://127.0.0.1:{BACKEND_PORT}")
