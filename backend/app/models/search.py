from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, JSON, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class SearchStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class Search(Base):
    __tablename__ = "searches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    # critérios
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    max_price: Mapped[float] = mapped_column(Float, nullable=False)
    location: Mapped[str] = mapped_column(String(200), nullable=False)
    year_min: Mapped[int] = mapped_column(Integer, nullable=True)
    year_max: Mapped[int] = mapped_column(Integer, nullable=True)
    max_km: Mapped[int] = mapped_column(Integer, nullable=True)
    transmission: Mapped[str] = mapped_column(String(20), nullable=True)  # manual/automatico/indiferente
    fuel: Mapped[str] = mapped_column(String(20), nullable=True)

    status: Mapped[SearchStatus] = mapped_column(Enum(SearchStatus), default=SearchStatus.pending)
    fipe_value: Mapped[float] = mapped_column(Float, nullable=True)
    results: Mapped[dict] = mapped_column(JSON, nullable=True)
    total_found: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="searches")  # noqa: F821
