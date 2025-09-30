from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from .db import Base


class ProcessingHistory(Base):
    __tablename__ = "processing_history"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    format = Column(String, nullable=False)
    lufs_before = Column(Float, nullable=False)
    lufs_after = Column(Float, nullable=False)
    peak = Column(Float, nullable=False)
    target_lufs = Column(Float, nullable=False)
    plot_path = Column(String, nullable=True)  # 👈 новое поле
    created_at = Column(DateTime(timezone=True), server_default=func.now())
