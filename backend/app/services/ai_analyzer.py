import anthropic
import json
import logging
from app.schemas.search import CarListing, RankedResult
from app.config import get_settings
from app.services.resale_analyzer import calculate_resale_opportunity

logger = logging.getLogger(__name__)
settings = get_settings()

INSPECTION_CHECKLIST = [
    "Consultar histórico do veículo (DETRAN / Consulta Veicular)",
    "Verificar passagem por leilão",
    "Confirmar ausência de registro de sinistro grave",
    "Checar se a quilometragem é compatível com o ano e uso declarado",
    "Verificar documentação completa e sem restrições (IPVA, DPVAT, multas)",
    "Avaliar pneus, suspensão, amortecedores e possíveis vazamentos",
    "Testar câmbio, freios, ar-condicionado e parte elétrica",
    "Verificar histórico de manutenção e revisões",
    "Exigir laudo de vistoria cautelar antes de fechar negócio",
    "Conferir número do chassi no documento e no veículo",
]


class AIAnalyzer:
    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def rank_and_analyze(
        self,
        listings: list[CarListing],
        fipe_value: float,
        criteria_summary: str,
        include_resale: bool = False,
        fraud_results: dict | None = None,
    ) -> tuple[list[RankedResult], str, str]:
        if not listings:
            return [], "Nenhum resultado encontrado.", "Nenhum resultado encontrado."

        # Enriquece os dados antes de enviar para IA
        listings_enriched = []
        for l in listings[:30]:
            item = l.model_dump()
            diff_pct = ((l.price - fipe_value) / fipe_value) * 100 if fipe_value else 0
            item["fipe_diff_pct"] = round(diff_pct, 1)
            fraud = fraud_results.get(l.url, {}) if fraud_results else {}
            item["fraud_score"] = fraud.get("fraud_score", 0)
            item["fraud_flags"] = fraud.get("flags", [])
            if include_resale and fipe_value:
                resale = calculate_resale_opportunity(l.price, fipe_value, l.km, l.year)
                item["resale_roi_pct"] = resale.roi_pct
                item["resale_net_margin"] = resale.net_margin
                item["resale_opportunity"] = resale.opportunity_label
            listings_enriched.append(item)

        resale_instruction = ""
        if include_resale:
            resale_instruction = "\nInclua no JSON um campo 'resale_summary' com avaliação da oportunidade de revenda em 1 frase."

        prompt = f"""Você é um especialista em mercado automotivo brasileiro. Analise e rankei os anúncios abaixo.

CRITÉRIOS: {criteria_summary}
FIPE: R$ {fipe_value:,.0f}

ANÚNCIOS (já calculado fipe_diff_pct e fraud_score):
{json.dumps(listings_enriched, ensure_ascii=False, indent=2)}

Calcule o ranking definitivo de custo-benefício considerando: preço vs FIPE, km, estado e fraud_score.
Um fraud_score > 50 deve penalizar fortemente o ranking.{resale_instruction}

Responda SOMENTE com JSON válido:
{{
  "ranking": [
    {{
      "position": 1,
      "listing_url": "url",
      "fipe_diff_pct": -8.5,
      "verdict": "vale muito a pena",
      "strengths": ["item"],
      "risks": ["item"],
      "summary": "frase"
    }}
  ],
  "best_choice": "texto",
  "cheapest_choice": "texto"
}}

Ordene do mais ao menos vantajoso. Inclua todos os anúncios."""

        try:
            response = await self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=5000,
                system="Especialista em mercado automotivo brasileiro. Responda sempre em JSON válido.",
                messages=[{"role": "user", "content": prompt}],
            )
            content = response.content[0].text.strip()
            if content.startswith("```"):
                content = content.split("```")[1].lstrip("json").strip()
            data = json.loads(content)
            listing_map = {l.url: l for l in listings}

            ranked = []
            for item in data.get("ranking", []):
                url = item.get("listing_url", "")
                listing = listing_map.get(url)
                if not listing:
                    idx = item.get("position", 1) - 1
                    if 0 <= idx < len(listings):
                        listing = listings[idx]
                if not listing:
                    continue

                resale_data = None
                if include_resale and fipe_value:
                    resale_data = calculate_resale_opportunity(
                        listing.price, fipe_value, listing.km, listing.year
                    ).__dict__

                ranked.append(RankedResult(
                    position=item["position"],
                    listing=listing,
                    fipe_value=fipe_value,
                    fipe_diff_pct=item.get("fipe_diff_pct", 0),
                    verdict=item.get("verdict", "atenção"),
                    strengths=item.get("strengths", []),
                    risks=item.get("risks", []),
                    summary=item.get("summary", ""),
                    resale=resale_data,
                ))

            return ranked, data.get("best_choice", ""), data.get("cheapest_choice", "")

        except Exception as e:
            logger.error(f"AI analyzer error: {e}")
            return self._fallback_rank(listings, fipe_value, include_resale, fraud_results)

    def _fallback_rank(self, listings, fipe_value, include_resale, fraud_results):
        sorted_listings = sorted(listings, key=lambda l: l.price)
        ranked = []
        for i, l in enumerate(sorted_listings[:10]):
            diff_pct = ((l.price - fipe_value) / fipe_value) * 100 if fipe_value else 0
            fraud = (fraud_results or {}).get(l.url, {})
            fs = fraud.get("fraud_score", 0)
            if fs > 70:
                verdict = "evitar"
            elif diff_pct < -5 and fs < 30:
                verdict = "vale muito a pena"
            elif diff_pct <= 5:
                verdict = "vale a pena"
            elif diff_pct <= 15:
                verdict = "atenção"
            else:
                verdict = "evitar"

            resale_data = None
            if include_resale and fipe_value:
                resale_data = calculate_resale_opportunity(l.price, fipe_value, l.km, l.year).__dict__

            ranked.append(RankedResult(
                position=i + 1, listing=l, fipe_value=fipe_value,
                fipe_diff_pct=round(diff_pct, 1), verdict=verdict,
                strengths=[], risks=fraud.get("flags", []),
                summary=f"{diff_pct:+.1f}% vs FIPE",
                resale=resale_data,
            ))
        best = ranked[0].summary if ranked else ""
        cheapest = f"R$ {sorted_listings[0].price:,.0f}" if sorted_listings else ""
        return ranked, best, cheapest
