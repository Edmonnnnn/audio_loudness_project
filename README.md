🎧 Audio Loudness Normalizer & Tag Editor
Audio Loudness Normalizer & Tag Editor — это современный онлайн‑сервис для анализа, нормализации и пакетного редактирования аудиофайлов (MP3, WAV, FLAC), включая расширенную работу с тегами (ID3) и обложкой. Всё работает локально — ваши файлы и история не уходят во внешний интернет.

📦 Основные возможности
Нормализация аудио по LUFS и Peak
Поддержка MP3, WAV, FLAC. Настраиваемый Target LUFS, экспорт в выбранный формат, установка битрейта и пресетов.

Визуализация графика громкости
Автоматическая генерация графика изменения LUFS во времени для каждого трека.

PDF‑отчёт
Подробный отчёт по результатам обработки: исходные и итоговые параметры, график, все теги (включая расширенные поля), обложка.

История обработок
Вся история обработанных файлов доступна во вкладке History (сортировка, просмотр, обновление).

Редактор тегов MP3
Веб-UI для чтения, изменения и записи тегов (title, artist, album, date, genre, composer, discnumber, comment, albumartist, publisher, website, tracknumber), а также загрузка и встраивание обложки (JPEG/PNG).

Мгновенная нормализация редактируемого MP3
После изменения тегов можно сразу же нормализовать этот файл без повторной загрузки.

Тёмная/светлая тема интерфейса
Современный дизайн, доступность на мобильных устройствах.

Безопасность
Все временные файлы, история и пользовательские данные НЕ попадают в облако или интернет.

🛠️ Технологический стек
Backend:
Python 3.10+, FastAPI, SQLAlchemy, pyloudnorm, librosa, mutagen, reportlab, ffmpeg

Frontend:
HTML5, CSS3, Vanilla JS (без фреймворков)

База данных:
SQLite (автоматически создаётся в temp_files)

Обработка тегов:
mutagen (EasyID3 + ID3/APIC + кастомные поля)

Графики:
matplotlib

🚀 Как запустить проект локально
Склонируй репозиторий

bash
Копировать
Редактировать
git clone https://github.com/yourusername/audio_loudness_project.git
cd audio_loudness_project/backend
Установи зависимости
Убедись, что у тебя установлен Python 3.10+ и pip.

bash
Копировать
Редактировать
python -m venv venv
venv\Scripts\activate      # для Windows
# или source venv/bin/activate для Linux/macOS
pip install -r requirements.txt
requirements.txt:

nginx
Копировать
Редактировать
fastapi
uvicorn
sqlalchemy
mutagen
pyloudnorm
librosa
reportlab
matplotlib
python-multipart
psutil
Запусти backend и frontend

bash
Копировать
Редактировать
python run_all.py
FastAPI backend будет доступен на http://127.0.0.1:8000

Frontend — на http://localhost:3000

Открой сайт
Перейди в браузере на http://localhost:3000

🖥️ Как пользоваться
Normalize
Перейди на вкладку Normalize

Загрузить MP3, WAV или FLAC

Выбрать Target LUFS, формат вывода, битрейт, при необходимости — пресет

Нажать Normalize
Сервис скачает ZIP-архив с:

Normalized audio (в выбранном формате)

PDF‑отчётом (параметры, график, все теги, обложка)

(по возможности) PNG‑графиком LUFS

History
Смотри всю историю обработок, обновляй через Refresh

Просматривай параметры, графики, скачивай старые результаты

Tags
Загрузить MP3

Все теги отобразятся для редактирования (включая расширенные)

При необходимости загрузить обложку (JPG/PNG)

Нажать Save Tags
Изменения сохраняются в temp_files локально!

Можно сразу нажать Normalize This MP3
— аудиофайл обработается с новыми тегами, PDF будет содержать их все

🔑 Какие теги поддерживаются
Стандартные:
Title, Artist, Album, Genre, Date

Расширенные:
Composer, Disc Number, Comment, Album Artist, Publisher, Website, Track Number

Обложка (Cover Image):
Любое изображение JPEG/PNG, встроенное в MP3

🔥 Важные особенности
После изменения тегов на вкладке Tags НЕ нужно повторно загружать файл: используйте кнопку Normalize This MP3 — в отчёте будут свежие теги и обложка.

Все изменения остаются только на вашем компьютере — полная приватность.

В PDF-отчёте содержатся все теги и визуально вставленная обложка.

⚡️ Типовые ошибки и как их решить
Не скачивается ZIP:

Проверь, не блокирует ли браузер pop-ups/скачивание

Проверь, что выбраны все обязательные параметры

Посмотри логи сервера (в терминале)

Ошибка с тегами:

Используй только MP3, поддерживающий ID3v2

Некорректный формат обложки — только JPEG или PNG

Ошибка "file not found after tag edit":

Убедись, что имя файла совпадает с тем, который был загружен и изменён

🧪 Для тестировщика
Проверь по чек-листу:

Редактирование тегов:

Все стандартные и расширенные поля можно загрузить, изменить, сохранить и перезагрузить (Title, Artist, Album, Date, Genre, Composer, Disc Number, Comment, Album Artist, Publisher, Website, Track Number)

Загрузка и обновление обложки работают корректно

Ошибка обрабатывается при загрузке битого/пустого MP3

Нормализация:

Для любого поддерживаемого аудиоформата (MP3, WAV, FLAC) скачивается ZIP с PDF и графиком

В PDF-отчёте есть актуальные теги и обложка (после изменения на вкладке Tags и нажатия Normalize This MP3)

Корректно сохраняются параметры LUFS, Peak, график LUFS over time

История:

Корректно отображаются все обработки, сортируются по дате

Кнопка Refresh обновляет таблицу

UI/UX:

Переключение между вкладками работает без багов и зависаний

Вся информация корректно валидируется (обязательные поля, типы файлов)

Безопасность:

Нет утечек пользовательских данных

Все временные файлы хранятся только локально

🏗️ Архитектура
bash
Копировать
Редактировать
/audio_loudness_project/
  /backend/
    main.py
    run_all.py
    report_generator.py
    tags_editor.py
    audio_processor.py
    loudness_plot.py
    models.py
    db.py
    presets.py
    requirements.txt
    temp_files/
    output/plots/
  /frontend/
    index.html
    style.css
    script.js
    assets/










    🎧 Audio Loudness Normalizer & Tag Editor

Audio Loudness Normalizer & Tag Editor — это современный онлайн-сервис для анализа, нормализации и пакетного редактирования аудиофайлов (MP3, WAV, FLAC), включая расширенную работу с тегами (ID3) и обложкой.
Работает локально — ваши файлы и история не уходят в интернет.

📦 Возможности

Нормализация аудио по LUFS и Peak
MP3, WAV, FLAC. Настраиваемый Target LUFS, экспорт в выбранный формат, установка битрейта и пресетов.

Визуализация графика громкости
Автоматическая генерация графика изменения LUFS во времени.

PDF-отчёт
Итоговый файл с параметрами, графиком, тегами и обложкой.

История обработок
Локально хранится список обработанных файлов, сортировка и просмотр.

Редактор тегов
Все стандартные и расширенные поля (title, artist, album, genre, composer, publisher и др.) + загрузка/замена обложки.

Мгновенная нормализация изменённых MP3
После редактирования тегов можно сразу нормализовать.

Тёмная/светлая тема

Безопасность
Всё остаётся только на вашем компьютере.

🛠️ Технологии

Backend: Python 3.10+, FastAPI, SQLAlchemy, pyloudnorm, librosa, mutagen, ffmpeg-python, reportlab, matplotlib

Frontend: HTML5, CSS3, Vanilla JS

DB: SQLite (в temp_files/)

Обработка тегов: mutagen (EasyID3, APIC, расширенные поля)

Графики: matplotlib

FFmpeg: требуется установленный бинарник

🚀 Установка и запуск
1) Клонирование
git clone https://github.com/yourusername/audio_loudness_project.git
cd audio_loudness_project

2) Backend
cd backend
python -m venv .venv
.venv\Scripts\activate      # Windows
# или source .venv/bin/activate (Linux/macOS)

python -m pip install --upgrade pip wheel setuptools
pip install -r requirements.txt


requirements.txt:

fastapi>=0.110,<1.0
uvicorn[standard]>=0.27,<1.0
sqlalchemy>=2.0
mutagen>=1.47
pyloudnorm>=0.1
librosa>=0.10
reportlab>=4.1
matplotlib>=3.8
python-multipart>=0.0.9
psutil>=5.9
soundfile>=0.12
audioread>=3.0
ffmpeg-python>=0.2

3) Установка FFmpeg

Windows (без админ-прав):

Скачать FFmpeg build

Распаковать в backend/bin/ffmpeg/
(чтобы backend/bin/ffmpeg/bin/ffmpeg.exe существовал)

Добавить в PATH для сессии:

$env:PATH="C:\Users\User\Desktop\audio_loudness_project\backend\bin\ffmpeg\bin;$env:PATH"
ffmpeg -version


Linux/macOS:

sudo apt install ffmpeg
ffmpeg -version

4) Запуск backend
cd backend
.venv\Scripts\activate
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000


Swagger UI: http://127.0.0.1:8000/docs

5) Frontend

В новом терминале:

cd frontend
python -m http.server 3000


Открыть: http://localhost:3000

6) CORS (если нужно)

В main.py добавлен CORS:

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

🧪 Тестирование (чек-лист)

Normalize

Загрузи MP3/WAV/FLAC → выбери Target LUFS → Normalize

Скачивается ZIP → в нём аудио, PDF, PNG.

Tags

Загрузи MP3, измени теги и/или обложку → Save Tags

Нажми Normalize This MP3 → PDF содержит обновлённые теги.

History

Все прошлые обработки видны, сортировка по дате работает.

Кнопка Refresh обновляет список.

UI/UX

Переключение вкладок работает без багов.

Валидация обязательных полей и форматов файлов.

Security

Данные и история остаются локально.

Файлы в temp_files/ не уходят в сеть.

🔧 Возможные проблемы

ModuleNotFoundError → убедись, что используешь backend\.venv и зависимости из requirements.txt.

ffmpeg not found → проверь установку FFmpeg (ffmpeg -version).

CORS ошибка в браузере → проверь блок CORSMiddleware.

ZIP не скачивается → включи скачивание в браузере, проверь backend-логи.

🖥️ Удобный запуск в VS Code

Создай .vscode/launch.json:

{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Backend (uvicorn)",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["main:app","--reload","--host","127.0.0.1","--port","8000"],
      "cwd": "${workspaceFolder}/backend",
      "console": "integratedTerminal"
    },
    {
      "name": "Frontend (http.server 3000)",
      "type": "python",
      "request": "launch",
      "module": "http.server",
      "args": ["3000"],
      "cwd": "${workspaceFolder}/frontend",
      "console": "integratedTerminal"
    }
  ],
  "compounds": [
    {
      "name": "Run Project (Backend+Frontend)",
      "configurations": ["Backend (uvicorn)","Frontend (http.server 3000)"],
      "stopAll": true
    }
  ]
}


Запуск: Run Project (Backend+Frontend) → F5.

✅ Итог

Теперь проект полностью рабочий:

Backend (FastAPI + FFmpeg + аудио-обработка)

Frontend (Vanilla JS + http.server)

Все зависимости фиксированы в requirements.txt

Локальная работа без интернета и без лишних пакетов






fastapi>=0.110,<1.0
uvicorn[standard]>=0.27,<1.0
sqlalchemy>=2.0
mutagen>=1.47
pyloudnorm>=0.1
librosa>=0.10
reportlab>=4.1
matplotlib>=3.8
python-multipart>=0.0.9
psutil>=5.9
soundfile>=0.12
audioread>=3.0
ffmpeg-python>=0.2
