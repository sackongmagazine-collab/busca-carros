from sqlalchemy import String, Integer, ForeignKey, DateTime, Boolean, Enum, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class PlanTier(str, enum.Enum):
    free = "free"
    hunter = "hunter"
    hunter_pro = "hunter_pro"
    dealer = "dealer"


class SubscriptionStatus(str, enum.Enum):
    active = "active"
    past_due = "past_due"
    canceled = "canceled"
    trialing = "trialing"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    plan: Mapped[PlanTier] = mapped_column(Enum(PlanTier), default=PlanTier.free)
    status: Mapped[SubscriptionStatus] = mapped_column(Enum(SubscriptionStatus), default=SubscriptionStatus.active)

    stripe_customer_id: Mapped[str] = mapped_column(String(100), nullable=True, unique=True)
    stripe_subscription_id: Mapped[str] = mapped_column(String(100), nullable=True, unique=True)
    stripe_price_id: Mapped[str] = mapped_column(String(100), nullable=True)

    current_period_start: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_end: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    canceled_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)

    # métricas de uso do período atual
    searches_this_period: Mapped[int] = mapped_column(Integer, default=0)
    revenue_total: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="subscription")  # noqa: F821
