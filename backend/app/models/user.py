from sqlalchemy import String, Boolean, DateTime, Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class UserRole(str, enum.Enum):
    user = "user"
    dealer = "dealer"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    phone: Mapped[str] = mapped_column(String(30), nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.user)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    searches: Mapped[list["Search"]] = relationship("Search", back_populates="user")  # noqa: F821
    alerts: Mapped[list["Alert"]] = relationship("Alert", back_populates="user")  # noqa: F821
    subscription: Mapped["Subscription"] = relationship("Subscription", back_populates="user", uselist=False)  # noqa: F821
    dealer: Mapped["Dealer"] = relationship("Dealer", back_populates="user", uselist=False)  # noqa: F821

    @property
    def plan(self) -> str:
        if self.subscription:
            return self.subscription.plan.value
        return "free"

    @property
    def is_premium(self) -> bool:
        return self.plan in ("hunter", "hunter_pro", "dealer")
