from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, JSON, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class AlertChannel(str, enum.Enum):
    email = "email"
    whatsapp = "whatsapp"
    telegram = "telegram"


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    # critérios (idênticos ao SearchRequest)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    max_price: Mapped[float] = mapped_column(Float, nullable=False)
    location: Mapped[str] = mapped_column(String(200), nullable=False)
    year_min: Mapped[int] = mapped_column(Integer, nullable=True)
    year_max: Mapped[int] = mapped_column(Integer, nullable=True)
    max_km: Mapped[int] = mapped_column(Integer, nullable=True)
    transmission: Mapped[str] = mapped_column(String(20), default="indiferente")
    fuel: Mapped[str] = mapped_column(String(20), default="indiferente")

    # alerta dispara apenas abaixo de X% da FIPE (ex: -10 = 10% abaixo)
    fipe_threshold_pct: Mapped[float] = mapped_column(Float, default=0.0)

    # canais habilitados
    channels: Mapped[list] = mapped_column(JSON, default=list)  # ["email", "whatsapp"]

    # contato destino por canal
    whatsapp_number: Mapped[str] = mapped_column(String(30), nullable=True)  # +55119...
    telegram_chat_id: Mapped[str] = mapped_column(String(50), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_triggered_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)

    # IDs dos anúncios já notificados (evita reenvio)
    notified_listing_ids: Mapped[list] = mapped_column(JSON, default=list)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="alerts")  # noqa: F821
