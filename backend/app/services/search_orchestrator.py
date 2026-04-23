import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from datetime import datetime, timezone

from app.models.search import Search, SearchStatus
from app.schemas.search import SearchRequest, SearchResponse, CarListing
from app.services.fipe_service import FipeService
from app.services.mercadolivre_service import MercadoLivreService
from app.services.webmotors_scraper import WebmotorsScraper
from app.services.olx_service import OLXService
from app.services.ai_analyzer import AIAnalyzer, INSPECTION_CHECKLIST

logger = logging.getLogger(__name__)


class SearchOrchestrator:
    def __init__(self):
        self.fipe = FipeService()
        self.ml = MercadoLivreService()
        self.webmotors = WebmotorsScraper()
        self.olx = OLXService()
        self.ai = AIAnalyzer()

    async def run(self, search_id: int, criteria: SearchRequest, db: AsyncSession) -> SearchResponse:
        await self._set_status(db, search_id, SearchStatus.running)

        try:
            fipe_year = criteria.year_min or criteria.year_max

            # Busca todas as fontes em paralelo
            fipe_value, ml_results, wm_results, olx_results = await asyncio.gather(
                self.fipe.get_fipe_value(criteria.model, fipe_year),
                self.ml.search(criteria),
                self.webmotors.search(criteria),
                self.olx.search(criteria),
                return_exceptions=True,
            )

            if isinstance(fipe_value, Exception):
                logger.error(f"FIPE falhou: {fipe_value}")
                fipe_value = None
            if isinstance(ml_results, Exception):
                logger.warning(f"ML falhou: {ml_results}")
                ml_results = []
            if isinstance(wm_results, Exception):
                logger.warning(f"Webmotors falhou: {wm_results}")
                wm_results = []
            if isinstance(olx_results, Exception):
                logger.warning(f"OLX falhou: {olx_results}")
                olx_results = []

            logger.info(
                f"Busca {search_id}: ML={len(ml_results)} WM={len(wm_results)} OLX={len(olx_results)}"
            )

            all_listings: list[CarListing] = (ml_results or []) + (wm_results or []) + (olx_results or [])
            all_listings = self._deduplicate(all_listings)
            all_listings = self._apply_filters(all_listings, criteria)
            all_listings.sort(key=lambda l: l.price)

            fipe_value = fipe_value or 85000.0
            criteria_summary = (
                f"Modelo: {criteria.model} | "
                f"Preço máx: R${criteria.max_price:,.0f} | "
                f"Local: {criteria.location} | "
                f"Ano: {criteria.year_min or 'qualquer'}-{criteria.year_max or 'qualquer'} | "
                f"Câmbio: {criteria.transmission} | Combustível: {criteria.fuel}"
            )

            ranking, best_choice, cheapest_choice = await self.ai.rank_and_analyze(
                all_listings, fipe_value, criteria_summary
            )

            # Se não encontrou nenhum anúncio, melhorar a mensagem do best_choice
            if not all_listings:
                best_choice = (
                    f"Nenhum anúncio encontrado nas fontes disponíveis. "
                    f"Referência FIPE para {criteria.model}: R$ {fipe_value:,.0f}. "
                    f"Tente buscar diretamente no MercadoLivre, OLX ou Webmotors."
                )
                cheapest_choice = None

            response = SearchResponse(
                search_id=search_id,
                status="completed",
                fipe_value=fipe_value,
                total_found=len(all_listings),
                ranking=ranking,
                best_choice=best_choice,
                cheapest_choice=cheapest_choice,
                inspection_checklist=INSPECTION_CHECKLIST,
            )

            await self._save_results(db, search_id, response, fipe_value)
            return response

        except Exception as e:
            logger.error(f"Falha na busca {search_id}: {e}", exc_info=True)
            await self._set_status(db, search_id, SearchStatus.failed)
            raise

    def _deduplicate(self, listings: list[CarListing]) -> list[CarListing]:
        seen: set = set()
        unique = []
        for listing in listings:
            key = (
                round(listing.price / 1000),
                listing.year,
                round(listing.km / 5000) if listing.km else 0,
                (listing.location or "")[:8],
            )
            if key not in seen:
                seen.add(key)
                unique.append(listing)
        return unique

    def _apply_filters(self, listings: list[CarListing], c: SearchRequest) -> list[CarListing]:
        filtered = []
        for listing in listings:
            if listing.price > c.max_price:
                continue
            if c.max_km and listing.km and listing.km > c.max_km:
                continue
            if c.year_min and listing.year and listing.year < c.year_min:
                continue
            if c.year_max and listing.year and listing.year > c.year_max:
                continue
            filtered.append(listing)
        return filtered

    async def _set_status(self, db: AsyncSession, search_id: int, status: SearchStatus):
        await db.execute(
            update(Search).where(Search.id == search_id).values(status=status)
        )
        await db.commit()

    async def _save_results(self, db: AsyncSession, search_id: int, response: SearchResponse, fipe_value: float):
        results_dict = response.model_dump()
        await db.execute(
            update(Search).where(Search.id == search_id).values(
                status=SearchStatus.completed,
                fipe_value=fipe_value,
                results=results_dict,
                total_found=response.total_found,
                completed_at=datetime.now(timezone.utc),
            )
        )
        await db.commit()

    async def close(self):
        await asyncio.gather(
            self.fipe.close(),
            self.ml.close(),
            self.webmotors.close(),
            self.olx.close(),
        )
