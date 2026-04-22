from sqlalchemy import String, Integer, ForeignKey, DateTime, Float, JSON, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.database import Base


class FraudReport(Base):
    __tablename__ = "fraud_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    listing_url: Mapped[str] = mapped_column(String(1000), nullable=False, index=True)
    listing_source: Mapped[str] = mapped_column(String(50), nullable=False)
    listing_title: Mapped[str] = mapped_column(String(500), nullable=True)
    listing_price: Mapped[float] = mapped_column(Float, nullable=True)
    fipe_value: Mapped[float] = mapped_column(Float, nullable=True)

    fraud_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0-100
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)  # low/medium/high/critical
    flags: Mapped[list] = mapped_column(JSON, default=list)
    ai_analysis: Mapped[str] = mapped_column(Text, nullable=True)

    reported_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    admin_notes: Mapped[str] = mapped_column(Text, nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
