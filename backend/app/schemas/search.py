from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class TransmissionEnum(str, Enum):
    manual = "manual"
    automatico = "automatico"
    indiferente = "indiferente"


class FuelEnum(str, Enum):
    flex = "flex"
    gasolina = "gasolina"
    diesel = "diesel"
    eletrico = "eletrico"
    indiferente = "indiferente"


class SearchRequest(BaseModel):
    model: str = Field(..., min_length=2, max_length=100)
    max_price: float = Field(..., gt=0)
    location: str = Field(..., min_length=2, max_length=200)
    year_min: Optional[int] = Field(None, ge=1990, le=2026)
    year_max: Optional[int] = Field(None, ge=1990, le=2026)
    max_km: Optional[int] = Field(None, ge=0)
    transmission: TransmissionEnum = TransmissionEnum.indiferente
    fuel: FuelEnum = FuelEnum.indiferente
    include_resale_analysis: bool = False  # disponível Hunter Pro+


class CarListing(BaseModel):
    source: str
    title: str
    model: str
    year: Optional[int] = None
    price: float
    km: Optional[int] = None
    transmission: Optional[str] = None
    fuel: Optional[str] = None
    location: str
    url: str
    image_url: Optional[str] = None
    seller_type: Optional[str] = None


class FraudInfo(BaseModel):
    fraud_score: float = 0.0
    risk_level: str = "low"
    flags: list[str] = []


class ResaleInfo(BaseModel):
    buy_price: float
    fipe_value: float
    estimated_resale_price: float
    reconditioning_estimate: float
    platform_fee: float
    transfer_costs: float
    gross_margin: float
    net_margin: float
    roi_pct: float
    payback_months: float
    opportunity_score: float
    opportunity_label: str
    breakdown: dict


class RankedResult(BaseModel):
    position: int
    listing: CarListing
    fipe_value: float
    fipe_diff_pct: float
    verdict: str
    strengths: list[str]
    risks: list[str]
    summary: str
    fraud: Optional[FraudInfo] = None
    resale: Optional[dict] = None  # ResaleInfo dict quando disponível


class SearchResponse(BaseModel):
    search_id: int
    status: str
    fipe_value: Optional[float] = None
    total_found: int = 0
    ranking: list[RankedResult] = []
    best_choice: Optional[str] = None
    cheapest_choice: Optional[str] = None
    inspection_checklist: list[str] = []
