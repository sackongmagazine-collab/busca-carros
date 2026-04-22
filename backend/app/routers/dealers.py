from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models.dealer import Dealer, DealerListing
from app.models.subscription import PlanTier
from app.routers.auth import get_current_user_required
from app.services.fraud_detector import FraudDetector
from app.schemas.search import CarListing

router = APIRouter(prefix="/dealers", tags=["dealers"])


class DealerUpdate(BaseModel):
    company_name: Optional[str] = None
    cnpj: Optional[str] = None
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None


class ListingCreate(BaseModel):
    make: str
    model: str
    version: Optional[str] = None
    year_fab: int
    year_model: int
    color: Optional[str] = None
    km: int
    transmission: str
    fuel: str
    doors: int = 4
    plate_end: Optional[str] = None
    price: float
    accepts_trade: bool = False
    is_financed: bool = True
    photos: list[str] = []
    video_url: Optional[str] = None
    description: Optional[str] = None
    features: list[str] = []


# ─── Perfil do lojista ────────────────────────────────────────────────────────

@router.get("/me")
async def get_my_dealer_profile(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_required),
):
    _require_dealer_plan(current_user)
    dealer = await _get_dealer(current_user.id, db)
    return _dealer_dict(dealer)


@router.patch("/me")
async def update_dealer_profile(
    data: DealerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_required),
):
    _require_dealer_plan(current_user)
    dealer = await _get_dealer(current_user.id, db)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(dealer, field, value)
    await db.commit()
    return _dealer_dict(dealer)


# ─── Listagens do lojista ─────────────────────────────────────────────────────

@router.get("/me/listings")
async def get_my_listings(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_required),
):
    _require_dealer_plan(current_user)
    dealer = await _get_dealer(current_user.id, db)
    query = select(DealerListing).where(DealerListing.dealer_id == dealer.id)
    if active_only:
        query = query.where(DealerListing.is_active == True)
    result = await db.execute(query.order_by(DealerListing.created_at.desc()))
    return [_listing_dict(l) for l in result.scalars().all()]


@router.post("/me/listings", status_code=201)
async def create_listing(
    data: ListingCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_required),
):
    _require_dealer_plan(current_user)
    dealer = await _get_dealer(current_user.id, db)

    from app.config import get_settings
    settings = get_settings()
    if dealer.active_listings >= settings.dealer_max_listings:
        raise HTTPException(status_code=403, detail="Limite de anúncios ativos atingido")

    # Antifraude automático na criação
    fraud = FraudDetector()
    fake_listing = CarListing(
        source="dealer",
        title=f"{data.make} {data.model} {data.version or ''}".strip(),
        model=data.model,
        year=data.year_model,
        price=data.price,
        km=data.km,
        transmission=data.transmission,
        fuel=data.fuel,
        location=f"{dealer.city or ''}/{dealer.state or ''}",
        url="",
        seller_type="loja",
    )
    fraud_result = await fraud.analyze(fake_listing, 0)

    listing = DealerListing(
        dealer_id=dealer.id,
        fraud_score=fraud_result["fraud_score"],
        fraud_flags=fraud_result["flags"],
        is_flagged=fraud_result["is_suspicious"],
        **data.model_dump(),
    )
    db.add(listing)

    dealer.total_listings += 1
    dealer.active_listings += 1
    await db.commit()
    await db.refresh(listing)
    return _listing_dict(listing)


@router.patch("/me/listings/{listing_id}")
async def update_listing(
    listing_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_required),
):
    _require_dealer_plan(current_user)
    dealer = await _get_dealer(current_user.id, db)
    listing = await _get_listing(listing_id, dealer.id, db)
    allowed_fields = {"price", "km", "description", "photos", "video_url", "is_active", "features", "accepts_trade"}
    for k, v in data.items():
        if k in allowed_fields:
            setattr(listing, k, v)
    await db.commit()
    return _listing_dict(listing)


@router.delete("/me/listings/{listing_id}", status_code=204)
async def delete_listing(
    listing_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_required),
):
    _require_dealer_plan(current_user)
    dealer = await _get_dealer(current_user.id, db)
    listing = await _get_listing(listing_id, dealer.id, db)
    listing.is_active = False
    dealer.active_listings = max(0, dealer.active_listings - 1)
    await db.commit()


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _require_dealer_plan(user):
    if user.plan != PlanTier.dealer.value:
        raise HTTPException(status_code=403, detail="Acesso exclusivo ao plano Lojista (Dealer).")


async def _get_dealer(user_id: int, db: AsyncSession) -> Dealer:
    result = await db.execute(select(Dealer).where(Dealer.user_id == user_id))
    dealer = result.scalar_one_or_none()
    if not dealer:
        raise HTTPException(status_code=404, detail="Perfil de lojista não encontrado")
    return dealer


async def _get_listing(listing_id: int, dealer_id: int, db: AsyncSession) -> DealerListing:
    result = await db.execute(
        select(DealerListing).where(DealerListing.id == listing_id, DealerListing.dealer_id == dealer_id)
    )
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Anúncio não encontrado")
    return listing


def _dealer_dict(d: Dealer) -> dict:
    return {
        "id": d.id, "company_name": d.company_name, "cnpj": d.cnpj,
        "phone": d.phone, "whatsapp": d.whatsapp, "city": d.city,
        "state": d.state, "website": d.website, "description": d.description,
        "logo_url": d.logo_url, "is_verified": d.is_verified,
        "is_featured": d.is_featured, "rating": d.rating,
        "total_listings": d.total_listings, "active_listings": d.active_listings,
        "total_views": d.total_views, "total_leads": d.total_leads,
    }


def _listing_dict(l: DealerListing) -> dict:
    return {
        "id": l.id, "make": l.make, "model": l.model, "version": l.version,
        "year_fab": l.year_fab, "year_model": l.year_model, "color": l.color,
        "km": l.km, "transmission": l.transmission, "fuel": l.fuel,
        "price": l.price, "fipe_value": l.fipe_value, "accepts_trade": l.accepts_trade,
        "is_financed": l.is_financed, "photos": l.photos, "video_url": l.video_url,
        "description": l.description, "features": l.features,
        "is_active": l.is_active, "is_featured": l.is_featured,
        "views": l.views, "leads": l.leads,
        "fraud_score": l.fraud_score, "fraud_flags": l.fraud_flags, "is_flagged": l.is_flagged,
        "created_at": l.created_at.isoformat() if l.created_at else None,
    }
