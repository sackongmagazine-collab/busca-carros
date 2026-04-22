"""
Calcula a oportunidade de revenda de cada anúncio.

Modelo de cálculo:
  preço_revenda_estimado = fipe_value * ajuste_km * ajuste_estado
  custo_recondicamento = estimado por IA baseado no estado do anúncio
  margem_bruta = preço_revenda - preço_compra - recondicamento - taxas_plataforma
  roi = margem_bruta / preço_compra
"""

from dataclasses import dataclass
from typing import Optional
import math


PLATFORM_FEE_PCT = 0.03          # 3% taxa média plataforma de revenda
FINANCING_COST_PCT = 0.015       # custo de capital médio
IPVA_TRANSFER_ESTIMATE = 1200    # custo médio transferência + IPVA proporcional
BASE_RECON_COST = 800            # limpeza, revisão básica, fotos profissionais


@dataclass
class ResaleOpportunity:
    buy_price: float
    fipe_value: float
    estimated_resale_price: float
    reconditioning_estimate: float
    platform_fee: float
    transfer_costs: float
    gross_margin: float
    net_margin: float
    roi_pct: float
    payback_months: float           # tempo estimado de estoque
    opportunity_score: float        # 0-100
    opportunity_label: str          # excelente / boa / marginal / negativa
    breakdown: dict                 # detalhamento linha a linha


def calculate_resale_opportunity(
    buy_price: float,
    fipe_value: float,
    km: Optional[int] = None,
    year: Optional[int] = None,
    has_full_description: bool = True,
    fraud_score: float = 0.0,
) -> ResaleOpportunity:

    # 1. Estima preço de revenda ajustado por km
    km_factor = _km_depreciation_factor(km, year)
    estimated_resale = fipe_value * km_factor

    # 2. Estimativa de recondicionamento
    km_recon = _km_reconditioning_cost(km)
    desc_penalty = 0 if has_full_description else 500
    recon_total = BASE_RECON_COST + km_recon + desc_penalty

    # 3. Taxas e custos fixos
    platform_fee = estimated_resale * PLATFORM_FEE_PCT
    capital_cost = buy_price * FINANCING_COST_PCT
    total_costs = recon_total + platform_fee + IPVA_TRANSFER_ESTIMATE + capital_cost

    # 4. Margens
    gross_margin = estimated_resale - buy_price
    net_margin = gross_margin - total_costs
    roi_pct = (net_margin / buy_price) * 100 if buy_price > 0 else 0

    # 5. Tempo estimado de estoque (modelo simplificado por faixa de preço)
    payback_months = _estimate_payback(buy_price, roi_pct)

    # 6. Score de oportunidade (0-100)
    opportunity_score = _score(roi_pct, gross_margin, fraud_score)
    opportunity_label = _label(opportunity_score)

    return ResaleOpportunity(
        buy_price=round(buy_price, 2),
        fipe_value=round(fipe_value, 2),
        estimated_resale_price=round(estimated_resale, 2),
        reconditioning_estimate=round(recon_total, 2),
        platform_fee=round(platform_fee, 2),
        transfer_costs=IPVA_TRANSFER_ESTIMATE,
        gross_margin=round(gross_margin, 2),
        net_margin=round(net_margin, 2),
        roi_pct=round(roi_pct, 1),
        payback_months=round(payback_months, 1),
        opportunity_score=round(opportunity_score, 1),
        opportunity_label=opportunity_label,
        breakdown={
            "compra": buy_price,
            "revenda_estimada": round(estimated_resale, 2),
            "recondicionamento": round(recon_total, 2),
            "taxa_plataforma": round(platform_fee, 2),
            "transferencia_ipva": IPVA_TRANSFER_ESTIMATE,
            "custo_capital": round(capital_cost, 2),
            "margem_bruta": round(gross_margin, 2),
            "margem_liquida": round(net_margin, 2),
            "roi_pct": round(roi_pct, 1),
        },
    )


def _km_depreciation_factor(km: Optional[int], year: Optional[int]) -> float:
    if not km:
        return 0.95
    from datetime import date
    current_year = date.today().year
    age = current_year - (year or current_year)
    expected_km = max(age * 15000, 1)  # 15k km/ano referência
    ratio = km / expected_km
    if ratio < 0.5:
        return 1.05   # muito rodado abaixo do esperado — premium
    elif ratio < 0.8:
        return 1.0
    elif ratio < 1.2:
        return 0.97
    elif ratio < 1.8:
        return 0.93
    else:
        return 0.88   # muito rodado


def _km_reconditioning_cost(km: Optional[int]) -> float:
    if not km:
        return 500
    if km < 30000:
        return 200
    elif km < 80000:
        return 600
    elif km < 150000:
        return 1200
    else:
        return 2500


def _estimate_payback(buy_price: float, roi_pct: float) -> float:
    if buy_price < 40000:
        return 1.5
    elif buy_price < 80000:
        return 2.5
    elif buy_price < 150000:
        return 3.5
    else:
        return 4.5


def _score(roi_pct: float, gross_margin: float, fraud_score: float) -> float:
    roi_score = min(max(roi_pct * 3, 0), 60)
    margin_score = min(gross_margin / 1000, 30)
    fraud_penalty = fraud_score * 0.5
    return max(roi_score + margin_score - fraud_penalty, 0)


def _label(score: float) -> str:
    if score >= 70:
        return "excelente"
    elif score >= 45:
        return "boa"
    elif score >= 20:
        return "marginal"
    else:
        return "negativa"
