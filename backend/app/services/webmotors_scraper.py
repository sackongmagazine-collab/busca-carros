import httpx
import logging
import asyncio
from typing import Optional
from app.schemas.search import CarListing, SearchRequest

logger = logging.getLogger(__name__)

WM_API = "https://www.webmotors.com.br/api/search/car"


class WebmotorsScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Referer": "https://www.webmotors.com.br/",
        }
        self.client = httpx.AsyncClient(timeout=20.0, headers=self.headers, follow_redirects=True)

    async def search(self, criteria: SearchRequest) -> list[CarListing]:
        listings = []
        for attempt in range(3):
            try:
                params = {
                    "url": self._build_url(criteria),
                    "actualPage": 1,
                    "displayPerPage": 24,
                    "order": 1,
                    "showMenu": False,
                }
                resp = await self.client.get(WM_API, params=params)
                if resp.status_code in (429, 403):
                    wait = 2 ** attempt
                    logger.warning(f"Webmotors bloqueado ({resp.status_code}), aguardando {wait}s")
                    await asyncio.sleep(wait)
                    continue
                resp.raise_for_status()
                data = resp.json()
                for item in data.get("SearchResults", []):
                    listing = self._parse_item(item, criteria)
                    if listing:
                        listings.append(listing)
                break
            except httpx.TimeoutException:
                logger.warning(f"Webmotors timeout (tentativa {attempt+1})")
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
            except Exception as e:
                logger.warning(f"Webmotors indisponível: {e}")
                break
        return listings

    def _build_url(self, c: SearchRequest) -> str:
        parts = ["https://www.webmotors.com.br/carros"]
        model_slug = c.model.lower().replace(" ", "-")
        parts.append(model_slug)
        if c.location:
            location_slug = c.location.lower().replace(" ", "-")
            parts.append(location_slug)
        return "/".join(parts)

    def _parse_item(self, item: dict, criteria: SearchRequest) -> Optional[CarListing]:
        try:
            spec = item.get("Specification", {})
            price_info = item.get("Prices", {})
            price = float(price_info.get("Price", 0))

            if not price or price > criteria.max_price:
                return None

            year = spec.get("YearFabrication")
            km = spec.get("Odometer")

            if criteria.max_km and km and int(km) > criteria.max_km:
                return None
            if criteria.year_min and year and int(year) < criteria.year_min:
                return None
            if criteria.year_max and year and int(year) > criteria.year_max:
                return None

            make = spec.get("Make", {}).get("Value", "")
            model = spec.get("Model", {}).get("Value", "")
            version = spec.get("Version", {}).get("Value", "")
            title = f"{make} {model} {version}".strip()

            city = item.get("Seller", {}).get("City", "")
            state = item.get("Seller", {}).get("State", "")

            unique_id = item.get("UniqueId", "")
            url = f"https://www.webmotors.com.br/carros/estoque/{unique_id}" if unique_id else ""

            return CarListing(
                source="Webmotors",
                title=title,
                model=criteria.model,
                year=int(year) if year else None,
                price=price,
                km=int(km) if km else None,
                transmission=spec.get("Transmission", ""),
                fuel=spec.get("FuelType", ""),
                location=f"{city}/{state}".strip("/"),
                url=url,
                image_url=item.get("Media", [{}])[0].get("LargeUrl") if item.get("Media") else None,
                seller_type="loja" if item.get("Seller", {}).get("IsProfessional") else "particular",
            )
        except Exception as e:
            logger.warning(f"Erro parse Webmotors: {e}")
            return None

    async def close(self):
        await self.client.aclose()
