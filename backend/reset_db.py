import os
from db import init_db

DB_PATH = "temp_files/history.db"

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print(f"[✓] Удалена база данных: {DB_PATH}")
else:
    print(f"[i] База данных уже удалена или не существует.")

init_db()
print("[✓] Создана новая база данных со всеми актуальными колонками.")
