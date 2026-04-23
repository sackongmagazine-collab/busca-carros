import httpx
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import logging
import time

logger = logging.getLogger(__name__)

FIPE_BASE = "https://parallelum.com.br/fipe/api/v2"
_cache: dict[str, tuple[float, float]] = {}  # key -> (value, expires_at)
_CACHE_TTL = 3600  # 1 hora


def _cached(key: str) -> Optional[float]:
    entry = _cache.get(key)
    if entry and time.time() < entry[1]:
        return entry[0]
    return None


def _set_cache(key: str, value: float):
    _cache[key] = (value, time.time() + _CACHE_TTL)


class FipeService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=15.0)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    async def _get(self, url: str) -> dict:
        resp = await self.client.get(url)
        resp.raise_for_status()
        return resp.json()

    async def search_brand(self, model_name: str) -> Optional[dict]:
        try:
            brands = await self._get(f"{FIPE_BASE}/cars/brands")
            model_lower = model_name.lower()
            brand_map = {
                "hb20": "hyundai", "creta": "hyundai", "tucson": "hyundai",
                "onix": "chevrolet", "tracker": "chevrolet", "cruze": "chevrolet",
                "ka": "ford", "ecosport": "ford", "ranger": "ford",
                "gol": "volkswagen", "polo": "volkswagen", "t-cross": "volkswagen",
                "kwid": "renault", "sandero": "renault", "duster": "renault",
                "mobi": "fiat", "uno": "fiat", "strada": "fiat", "argo": "fiat",
                "civic": "honda", "hr-v": "honda", "fit": "honda",
                "corolla": "toyota", "hilux": "toyota", "yaris": "toyota",
                "kicks": "nissan", "versa": "nissan",
                "compass": "jeep", "renegade": "jeep",
            }
            brand_name = brand_map.get(model_lower, model_lower.split()[0])
            for brand in brands:
                if brand_name in brand["name"].lower():
                    return brand
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar marca FIPE: {e}")
            return None

    async def get_fipe_value(self, model_name: str, year: Optional[int] = None) -> Optional[float]:
        cache_key = f"{model_name}:{year}"
        cached = _cached(cache_key)
        if cached:
            return cached

        try:
            brand = await self.search_brand(model_name)
            if not brand:
                val = await self._estimate_value(model_name)
                _set_cache(cache_key, val)
                return val

            models_data = await self._get(f"{FIPE_BASE}/cars/brands/{brand['code']}/models")
            model_lower = model_name.lower()
            matched_model = next(
                (m for m in models_data.get("models", []) if model_lower in m["name"].lower()),
                None
            )
            if not matched_model:
                val = await self._estimate_value(model_name)
                _set_cache(cache_key, val)
                return val

            years = await self._get(
                f"{FIPE_BASE}/cars/brands/{brand['code']}/models/{matched_model['code']}/years"
            )
            if not years:
                val = await self._estimate_value(model_name)
                _set_cache(cache_key, val)
                return val

            target_years = [y for y in years if year and str(year) in y["name"]] or years[:1]
            detail = await self._get(
                f"{FIPE_BASE}/cars/brands/{brand['code']}/models/{matched_model['code']}/years/{target_years[0]['code']}"
            )
            price_str = detail.get("price", "0")
            price = float(price_str.replace("R$ ", "").replace(".", "").replace(",", "."))
            _set_cache(cache_key, price)
            return price

        except Exception as e:
            logger.error(f"Erro FIPE para {model_name}: {e}")
            val = await self._estimate_value(model_name)
            _set_cache(cache_key, val)
            return val

    async def get_model_suggestions(self, query: str) -> list[str]:
        all_models = [
            "HB20", "HB20S", "Creta", "Tucson",
            "Onix", "Onix Plus", "Tracker", "Cruze", "S10", "Montana",
            "Ka", "Ecosport", "Ranger", "Territory",
            "Gol", "Polo", "Polo GTS", "T-Cross", "Virtus", "Saveiro", "Amarok",
            "Kwid", "Sandero", "Duster", "Logan",
            "Mobi", "Uno", "Argo", "Cronos", "Strada", "Toro", "Fiorino",
            "Civic", "HR-V", "Fit", "City", "WR-V",
            "Corolla", "Corolla Cross", "Hilux", "SW4", "Yaris", "RAV4",
            "Kicks", "Versa", "Frontier",
            "Compass", "Renegade", "Commander",
            "Spin", "Cobalt", "Captiva",
            "208", "2008", "3008",
            "Pulse", "Fastback",
            "Tiggo 5X", "Tiggo 7 Pro", "Tiggo 8 Pro",
        ]
        q = query.lower()
        return [m for m in all_models if q in m.lower()][:8]

    async def _estimate_value(self, model_name: str) -> float:
        estimates = {
            "hb20": 75000, "onix": 82000, "ka": 58000, "gol": 52000,
            "polo": 92000, "kwid": 62000, "mobi": 58000, "argo": 72000,
            "sandero": 68000, "uno": 48000, "fit": 72000, "civic": 125000,
            "corolla": 145000, "tracker": 108000, "creta": 115000,
            "hr-v": 115000, "kicks": 102000, "duster": 88000,
            "compass": 158000, "renegade": 118000, "t-cross": 105000,
            "ecosport": 88000, "hilux": 215000, "ranger": 195000,
            "strada": 112000, "s10": 185000,
        }
        key = model_name.lower().split()[0]
        return estimates.get(key, 85000)

    async def close(self):
        await self.client.aclose()
