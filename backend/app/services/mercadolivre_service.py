import httpx
import logging
import asyncio
from typing import Optional
from app.schemas.search import CarListing, SearchRequest

logger = logging.getLogger(__name__)

ML_API = "https://api.mercadolibre.com"


class MercadoLivreService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=20.0, headers={"User-Agent": "BuscaCarros/1.0"})

    async def search(self, criteria: SearchRequest) -> list[CarListing]:
        listings = []
        for attempt in range(3):
            try:
                query = criteria.model
                if criteria.year_min:
                    query += f" {criteria.year_min}"

                params = {
                    "q": query,
                    "category": "MLB1744",
                    "price": f"*-{int(criteria.max_price)}",
                    "sort": "price_asc",
                    "limit": 50,
                }
                if criteria.location:
                    state_map = self._resolve_state(criteria.location)
                    if state_map:
                        params["state"] = state_map

                resp = await self.client.get(f"{ML_API}/sites/MLB/search", params=params)
                if resp.status_code == 429:
                    wait = 2 ** attempt
                    logger.warning(f"ML rate limited, aguardando {wait}s")
                    await asyncio.sleep(wait)
                    continue
                resp.raise_for_status()
                data = resp.json()
                for item in data.get("results", []):
                    listing = self._parse_item(item, criteria)
                    if listing:
                        listings.append(listing)
                break
            except httpx.TimeoutException:
                logger.warning(f"ML timeout (tentativa {attempt+1})")
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
            except Exception as e:
                logger.error(f"Erro MercadoLivre: {e}")
                break
        return listings

    def _parse_item(self, item: dict, criteria: SearchRequest) -> Optional[CarListing]:
        try:
            attrs = {a["id"]: a.get("value_name") for a in item.get("attributes", [])}
            year = self._safe_int(attrs.get("VEHICLE_YEAR"))
            km = self._safe_int(attrs.get("KILOMETERS"))
            price = float(item.get("price", 0))

            if price > criteria.max_price:
                return None
            if criteria.max_km and km and km > criteria.max_km:
                return None
            if criteria.year_min and year and year < criteria.year_min:
                return None
            if criteria.year_max and year and year > criteria.year_max:
                return None

            return CarListing(
                source="MercadoLivre",
                title=item.get("title", ""),
                model=criteria.model,
                year=year,
                price=price,
                km=km,
                transmission=attrs.get("VEHICLE_TRANSMISSION"),
                fuel=attrs.get("FUEL_TYPE"),
                location=self._format_location(item),
                url=item.get("permalink", ""),
                image_url=item.get("thumbnail"),
                seller_type=item.get("seller", {}).get("eshop", {}).get("nick_name") and "loja" or "particular",
            )
        except Exception as e:
            logger.warning(f"Erro ao parsear item ML: {e}")
            return None

    def _format_location(self, item: dict) -> str:
        address = item.get("location", {})
        city = address.get("city", {}).get("name", "")
        state = address.get("state", {}).get("name", "")
        return f"{city}/{state}".strip("/")

    def _resolve_state(self, location: str) -> Optional[str]:
        location_lower = location.lower()
        state_codes = {
            "são paulo": "BR-SP", "sp": "BR-SP",
            "rio de janeiro": "BR-RJ", "rj": "BR-RJ",
            "minas gerais": "BR-MG", "mg": "BR-MG",
            "bahia": "BR-BA", "ba": "BR-BA",
            "paraná": "BR-PR", "pr": "BR-PR",
            "rio grande do sul": "BR-RS", "rs": "BR-RS",
            "goiás": "BR-GO", "go": "BR-GO",
            "pernambuco": "BR-PE", "pe": "BR-PE",
            "ceará": "BR-CE", "ce": "BR-CE",
            "santa catarina": "BR-SC", "sc": "BR-SC",
            "mato grosso do sul": "BR-MS", "ms": "BR-MS",
            "mato grosso": "BR-MT", "mt": "BR-MT",
            "distrito federal": "BR-DF", "df": "BR-DF",
            "brasília": "BR-DF",
        }
        for key, code in state_codes.items():
            if key in location_lower:
                return code
        return None

    def _safe_int(self, value) -> Optional[int]:
        try:
            return int(str(value).replace(".", "").replace(",", ""))
        except (ValueError, TypeError):
            return None

    async def close(self):
        await self.client.aclose()
