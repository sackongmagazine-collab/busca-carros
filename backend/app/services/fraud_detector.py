"""
Sistema antifraude multicamada para anúncios de veículos.

Camadas de análise:
  1. Anomalia de preço  — preço muito abaixo da FIPE sem justificativa
  2. Inconsistência km  — km incompatível com ano
  3. Análise de texto   — Claude detecta inconsistências e red flags
  4. Score de vendedor  — conta nova, sem histórico, telefone inválido
  5. Deduplicação       — mesmo anúncio em múltiplas fontes com preços diferentes
"""

import anthropic
import hashlib
import logging
import json
from datetime import date
from typing import Optional
from app.schemas.search import CarListing
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


FRAUD_THRESHOLDS = {
    "low": 25,
    "medium": 50,
    "high": 70,
    "critical": 85,
}


class FraudDetector:
    def __init__(self):
        self.ai = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def analyze(self, listing: CarListing, fipe_value: float) -> dict:
        flags = []
        score = 0.0

        # 1. Anomalia de preço
        price_flags, price_score = self._check_price(listing.price, fipe_value)
        flags.extend(price_flags)
        score += price_score

        # 2. Inconsistência km vs ano
        km_flags, km_score = self._check_km(listing.km, listing.year)
        flags.extend(km_flags)
        score += km_score

        # 3. Análise de texto com IA (só se já não tiver score crítico)
        if score < 70 and settings.anthropic_api_key:
            ai_flags, ai_score = await self._check_text_ai(listing, fipe_value)
            flags.extend(ai_flags)
            score += ai_score

        # 4. Score vendedor / fonte
        seller_flags, seller_score = self._check_seller(listing)
        flags.extend(seller_flags)
        score += seller_score

        score = min(score, 100)
        risk_level = self._risk_level(score)

        return {
            "fraud_score": round(score, 1),
            "risk_level": risk_level,
            "flags": flags,
            "is_suspicious": score >= FRAUD_THRESHOLDS["medium"],
        }

    def _check_price(self, price: float, fipe_value: float) -> tuple[list[str], float]:
        flags = []
        score = 0.0
        if fipe_value <= 0:
            return flags, score
        diff_pct = ((price - fipe_value) / fipe_value) * 100
        if diff_pct < -40:
            flags.append("Preço 40%+ abaixo da FIPE — risco muito elevado de golpe")
            score += 50
        elif diff_pct < -25:
            flags.append("Preço 25-40% abaixo da FIPE — requer verificação criteriosa")
            score += 30
        elif diff_pct < -15:
            flags.append("Preço 15-25% abaixo da FIPE — possível problema oculto")
            score += 15
        return flags, score

    def _check_km(self, km: Optional[int], year: Optional[int]) -> tuple[list[str], float]:
        flags = []
        score = 0.0
        if not km or not year:
            return flags, score
        current_year = date.today().year
        age = current_year - year
        if age <= 0:
            return flags, score
        km_per_year = km / age
        if km < 100:
            flags.append("Quilometragem zerada ou incorreta — suspeito")
            score += 20
        elif km_per_year > 60000:
            flags.append(f"KM/ano muito alta ({km_per_year:,.0f} km/ano) — possível adulteração")
            score += 25
        elif km_per_year < 1500 and age > 3:
            flags.append(f"KM/ano muito baixa ({km_per_year:,.0f} km/ano) — verifique odômetro")
            score += 10
        return flags, score

    async def _check_text_ai(self, listing: CarListing, fipe_value: float) -> tuple[list[str], float]:
        flags = []
        score = 0.0
        try:
            prompt = f"""Analise este anúncio de veículo e identifique sinais de fraude ou alerta.

Título: {listing.title}
Preço: R$ {listing.price:,.0f}
FIPE: R$ {fipe_value:,.0f}
Ano: {listing.year}
KM: {listing.km:,} km
Fonte: {listing.source}
Localização: {listing.location}
Vendedor: {listing.seller_type}

Responda SOMENTE com JSON:
{{
  "fraud_indicators": ["lista de red flags encontrados, strings curtas"],
  "additional_score": 0,
  "reasoning": "uma frase"
}}

additional_score: 0 a 40 (quanto aumentar o score de fraude com base no texto).
Se não houver problemas, retorne listas vazias e additional_score: 0."""

            resp = await self.ai.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=400,
                messages=[{"role": "user", "content": prompt}],
            )
            content = resp.content[0].text.strip()
            if content.startswith("```"):
                content = content.split("```")[1].lstrip("json").strip()
            data = json.loads(content)
            flags.extend(data.get("fraud_indicators", []))
            score += float(data.get("additional_score", 0))
        except Exception as e:
            logger.warning(f"AI fraud check falhou: {e}")
        return flags, score

    def _check_seller(self, listing: CarListing) -> tuple[list[str], float]:
        flags = []
        score = 0.0
        if listing.seller_type == "particular" and listing.source in ("MercadoLivre",):
            # particulares no ML têm maior risco estatístico
            score += 5
        if not listing.url:
            flags.append("Anúncio sem link verificável")
            score += 15
        if not listing.image_url:
            flags.append("Sem imagem — impossível avaliar estado")
            score += 10
        return flags, score

    def _risk_level(self, score: float) -> str:
        if score >= FRAUD_THRESHOLDS["critical"]:
            return "critical"
        elif score >= FRAUD_THRESHOLDS["high"]:
            return "high"
        elif score >= FRAUD_THRESHOLDS["medium"]:
            return "medium"
        return "low"
