import httpx
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

logger = logging.getLogger(__name__)

FIPE_BASE = "https://parallelum.com.br/fipe/api/v2"


class FipeService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=15.0)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def search_brand(self, model_name: str) -> Optional[dict]:
        """Busca marca pelo nome do modelo."""
        try:
            resp = await self.client.get(f"{FIPE_BASE}/cars/brands")
            resp.raise_for_status()
            brands = resp.json()
            model_lower = model_name.lower()
            # mapeia nomes comuns para marcas
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

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def get_fipe_value(self, model_name: str, year: Optional[int] = None) -> Optional[float]:
        """Retorna valor médio FIPE para o modelo/ano informado."""
        try:
            brand = await self.search_brand(model_name)
            if not brand:
                return await self._estimate_value(model_name)

            resp = await self.client.get(f"{FIPE_BASE}/cars/brands/{brand['code']}/models")
            resp.raise_for_status()
            models_data = resp.json()

            model_lower = model_name.lower()
            matched_model = None
            for m in models_data.get("models", []):
                if model_lower in m["name"].lower():
                    matched_model = m
                    break

            if not matched_model:
                return await self._estimate_value(model_name)

            years_resp = await self.client.get(
                f"{FIPE_BASE}/cars/brands/{brand['code']}/models/{matched_model['code']}/years"
            )
            years_resp.raise_for_status()
            years = years_resp.json()

            if not years:
                return await self._estimate_value(model_name)

            # Filtra pelo ano se fornecido, senão pega o mais recente
            target_years = [y for y in years if year and str(year) in y["name"]] or years[:1]
            target_year = target_years[0]

            detail_resp = await self.client.get(
                f"{FIPE_BASE}/cars/brands/{brand['code']}/models/{matched_model['code']}/years/{target_year['code']}"
            )
            detail_resp.raise_for_status()
            detail = detail_resp.json()

            price_str = detail.get("price", "0")
            price = float(price_str.replace("R$ ", "").replace(".", "").replace(",", "."))
            return price

        except Exception as e:
            logger.error(f"Erro FIPE para {model_name}: {e}")
            return await self._estimate_value(model_name)

    async def _estimate_value(self, model_name: str) -> float:
        """Estimativa de fallback baseada em conhecimento de mercado (2024)."""
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
