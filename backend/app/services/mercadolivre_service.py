import httpx
import logging
import asyncio
import unicodedata
from typing import Optional
from app.schemas.search import CarListing, SearchRequest

logger = logging.getLogger(__name__)

ML_API = "https://api.mercadolibre.com"

# Variações de nome por modelo para melhorar o recall
MODEL_ALIASES: dict[str, list[str]] = {
    "hb20": ["Hyundai HB20", "HB20"],
    "onix": ["Chevrolet Onix", "Onix"],
    "gol": ["Volkswagen Gol", "Gol"],
    "polo": ["Volkswagen Polo", "Polo"],
    "argo": ["Fiat Argo", "Argo"],
    "mobi": ["Fiat Mobi", "Mobi"],
    "uno": ["Fiat Uno", "Uno"],
    "ka": ["Ford Ka", "Ka"],
    "kwid": ["Renault Kwid", "Kwid"],
    "sandero": ["Renault Sandero", "Sandero"],
    "civic": ["Honda Civic", "Civic"],
    "corolla": ["Toyota Corolla", "Corolla"],
    "tracker": ["Chevrolet Tracker", "Tracker"],
    "creta": ["Hyundai Creta", "Creta"],
    "compass": ["Jeep Compass", "Compass"],
    "renegade": ["Jeep Renegade", "Renegade"],
    "t-cross": ["Volkswagen T-Cross", "T Cross"],
    "hilux": ["Toyota Hilux", "Hilux"],
    "ranger": ["Ford Ranger", "Ranger"],
    "strada": ["Fiat Strada", "Strada"],
    "kicks": ["Nissan Kicks", "Kicks"],
    "hr-v": ["Honda HR-V", "HRV"],
    "duster": ["Renault Duster", "Duster"],
    "ecosport": ["Ford EcoSport", "EcoSport"],
}


def _normalize(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower().strip()


class MercadoLivreService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=25.0, headers={"User-Agent": "BuscaCarros/2.0"})

    async def search(self, criteria: SearchRequest) -> list[CarListing]:
        model_norm = _normalize(criteria.model)
        queries = MODEL_ALIASES.get(model_norm, [criteria.model])

        for query in queries:
            listings = await self._search_query(query, criteria, with_state=True)
            if not listings:
                # Fallback: busca sem filtro de estado (abrangência nacional)
                listings = await self._search_query(query, criteria, with_state=False)
            if listings:
                return listings

        return []

    async def _search_query(self, query: str, criteria: SearchRequest, with_state: bool) -> list[CarListing]:
        for attempt in range(3):
            try:
                params: dict = {
                    "q": query,
                    "category": "MLB1744",
                    "price": f"*-{int(criteria.max_price)}",
                    "sort": "price_asc",
                    "limit": 50,
                }
                if with_state and criteria.location:
                    state_code = self._resolve_state(criteria.location)
                    if state_code:
                        params["state"] = state_code

                resp = await self.client.get(f"{ML_API}/sites/MLB/search", params=params)
                if resp.status_code == 429:
                    await asyncio.sleep(2 ** attempt)
                    continue
                resp.raise_for_status()
                data = resp.json()

                listings = []
                for item in data.get("results", []):
                    listing = self._parse_item(item, criteria)
                    if listing:
                        listings.append(listing)
                return listings

            except httpx.TimeoutException:
                logger.warning(f"ML timeout tentativa {attempt+1}")
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
            except Exception as e:
                logger.error(f"Erro MercadoLivre [{query}]: {e}")
                break
        return []

    def _parse_item(self, item: dict, criteria: SearchRequest) -> Optional[CarListing]:
        try:
            attrs = {a["id"]: a.get("value_name") for a in item.get("attributes", [])}
            year = self._safe_int(attrs.get("VEHICLE_YEAR"))
            km = self._safe_int(attrs.get("KILOMETERS"))
            price = float(item.get("price", 0))

            if price <= 0 or price > criteria.max_price:
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
                seller_type="loja" if item.get("official_store_id") else "particular",
            )
        except Exception as e:
            logger.warning(f"Erro parse item ML: {e}")
            return None

    def _format_location(self, item: dict) -> str:
        address = item.get("location", {})
        city = address.get("city", {}).get("name", "")
        state = address.get("state", {}).get("name", "")
        return f"{city}/{state}".strip("/")

    def _resolve_state(self, location: str) -> Optional[str]:
        loc = _normalize(location)
        state_codes = {
            "sao paulo": "BR-SP", "sp": "BR-SP",
            "rio de janeiro": "BR-RJ", "rj": "BR-RJ",
            "minas gerais": "BR-MG", "mg": "BR-MG",
            "bahia": "BR-BA", "ba": "BR-BA",
            "parana": "BR-PR", "pr": "BR-PR",
            "rio grande do sul": "BR-RS", "rs": "BR-RS",
            "goias": "BR-GO", "go": "BR-GO",
            "pernambuco": "BR-PE", "pe": "BR-PE",
            "ceara": "BR-CE", "ce": "BR-CE",
            "santa catarina": "BR-SC", "sc": "BR-SC",
            "mato grosso do sul": "BR-MS", "ms": "BR-MS",
            "mato grosso": "BR-MT", "mt": "BR-MT",
            "distrito federal": "BR-DF", "df": "BR-DF",
            "brasilia": "BR-DF", "espirito santo": "BR-ES", "es": "BR-ES",
            "amazonas": "BR-AM", "am": "BR-AM", "para": "BR-PA", "pa": "BR-PA",
            "maranhao": "BR-MA", "ma": "BR-MA", "piaui": "BR-PI", "pi": "BR-PI",
            "rio grande do norte": "BR-RN", "rn": "BR-RN",
            "paraiba": "BR-PB", "pb": "BR-PB", "sergipe": "BR-SE", "se": "BR-SE",
            "alagoas": "BR-AL", "al": "BR-AL", "tocantins": "BR-TO", "to": "BR-TO",
            "rondonia": "BR-RO", "ro": "BR-RO", "acre": "BR-AC", "ac": "BR-AC",
            "roraima": "BR-RR", "rr": "BR-RR", "amapa": "BR-AP", "ap": "BR-AP",
        }
        for key, code in state_codes.items():
            if key in loc:
                return code
        return None

    def _safe_int(self, value) -> Optional[int]:
        try:
            return int(str(value).replace(".", "").replace(",", ""))
        except (ValueError, TypeError):
            return None

    async def close(self):
        await self.client.aclose()
