import os
import subprocess
import shutil
import psutil
import time
import webbrowser

def kill_uvicorn_processes():
    print("[⛔] Ищем процессы uvicorn...")
    count = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and any("uvicorn" in str(part) for part in cmdline):
                proc.kill()
                count += 1
        except Exception as e:
            continue
    if count:
        print(f"[✓] Завершено процессов: {count}")
    else:
        print("[✓] Никаких процессов uvicorn не найдено.")

def cleanup():
    print("[🌐] Удаляем и пересоздаём базу данных и временные папки...")

    if os.path.exists("temp_files/history.db"):
        try:
            os.remove("temp_files/history.db")
            print("[✓] Удалена база данных: temp_files/history.db")
        except PermissionError:
            print("[!] Не удалось удалить history.db — занят другим процессом")
    
    shutil.rmtree("temp_files", ignore_errors=True)
    os.makedirs("temp_files", exist_ok=True)
    print("[✓] Папка temp_files очищена.")

    shutil.rmtree("output/plots", ignore_errors=True)
    os.makedirs("output/plots", exist_ok=True)
    print("[✓] Папка output/plots очищена.")

def run_backend():
    print("[🚀] Запускаем backend (FastAPI + Uvicorn)...")
    subprocess.Popen("uvicorn main:app --reload", shell=True)

def run_frontend():
    print("[🌐] Запускаем frontend (http://localhost:3000)...")
    os.chdir("../frontend")
    subprocess.Popen("python -m http.server 3000", shell=True)
    time.sleep(1)
    webbrowser.open("http://localhost:3000")
    os.chdir("../backend")

if __name__ == "__main__":
    kill_uvicorn_processes()
    time.sleep(1)
    cleanup()
    run_backend()
    time.sleep(2)
    run_frontend()
    print("[✅] Всё запущено! Сайт доступен на http://localhost:3000 и backend работает на http://127.0.0.1:8000")
