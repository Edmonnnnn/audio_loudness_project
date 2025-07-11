from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Путь к базе данных
DB_PATH = "temp_files/history.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# Создание движка SQLAlchemy
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Создание фабрики сессий и базового класса
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Функция инициализации базы (создание таблицы, если файла нет)
def init_db():
    if not os.path.exists(DB_PATH):
        from models import ProcessingHistory  # Импорт только при необходимости
        Base.metadata.create_all(bind=engine)
