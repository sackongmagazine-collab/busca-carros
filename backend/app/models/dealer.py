from sqlalchemy import String, Integer, ForeignKey, DateTime, Boolean, Float, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base


class Dealer(Base):
    __tablename__ = "dealers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    cnpj: Mapped[str] = mapped_column(String(20), nullable=True, unique=True)
    phone: Mapped[str] = mapped_column(String(30), nullable=True)
    whatsapp: Mapped[str] = mapped_column(String(30), nullable=True)
    address: Mapped[str] = mapped_column(String(500), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=True)
    state: Mapped[str] = mapped_column(String(2), nullable=True)
    website: Mapped[str] = mapped_column(String(300), nullable=True)
    logo_url: Mapped[str] = mapped_column(String(500), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)  # destaque pago
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    total_reviews: Mapped[int] = mapped_column(Integer, default=0)

    # métricas
    total_listings: Mapped[int] = mapped_column(Integer, default=0)
    active_listings: Mapped[int] = mapped_column(Integer, default=0)
    total_views: Mapped[int] = mapped_column(Integer, default=0)
    total_leads: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="dealer")  # noqa: F821
    listings: Mapped[list["DealerListing"]] = relationship("DealerListing", back_populates="dealer")  # noqa: F821


class DealerListing(Base):
    __tablename__ = "dealer_listings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dealer_id: Mapped[int] = mapped_column(Integer, ForeignKey("dealers.id"), nullable=False)

    # veículo
    make: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(200), nullable=True)
    year_fab: Mapped[int] = mapped_column(Integer, nullable=False)
    year_model: Mapped[int] = mapped_column(Integer, nullable=False)
    color: Mapped[str] = mapped_column(String(50), nullable=True)
    km: Mapped[int] = mapped_column(Integer, nullable=False)
    transmission: Mapped[str] = mapped_column(String(30), nullable=False)
    fuel: Mapped[str] = mapped_column(String(30), nullable=False)
    doors: Mapped[int] = mapped_column(Integer, default=4)
    plate_end: Mapped[str] = mapped_column(String(1), nullable=True)  # último dígito
    chassis: Mapped[str] = mapped_column(String(30), nullable=True)

    # preço
    price: Mapped[float] = mapped_column(Float, nullable=False)
    fipe_value: Mapped[float] = mapped_column(Float, nullable=True)
    accepts_trade: Mapped[bool] = mapped_column(Boolean, default=False)
    is_financed: Mapped[bool] = mapped_column(Boolean, default=True)

    # mídia
    photos: Mapped[list] = mapped_column(JSON, default=list)  # URLs
    video_url: Mapped[str] = mapped_column(String(500), nullable=True)

    # estado do anúncio
    description: Mapped[str] = mapped_column(Text, nullable=True)
    features: Mapped[list] = mapped_column(JSON, default=list)  # opcionais
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    views: Mapped[int] = mapped_column(Integer, default=0)
    leads: Mapped[int] = mapped_column(Integer, default=0)

    # antifraude
    fraud_score: Mapped[float] = mapped_column(Float, default=0.0)  # 0-100
    fraud_flags: Mapped[list] = mapped_column(JSON, default=list)
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    dealer: Mapped["Dealer"] = relationship("Dealer", back_populates="listings")  # noqa: F821
