import httpx
import logging
import asyncio
import json
import re
import unicodedata
from typing import Optional
from app.schemas.search import CarListing, SearchRequest

logger = logging.getLogger(__name__)

OLX_BASE = "https://www.olx.com.br"

STATE_SLUGS = {
    "sp": "sp", "são paulo": "sp", "sao paulo": "sp",
    "rj": "rj", "rio de janeiro": "rj",
    "mg": "mg", "minas gerais": "mg",
    "ba": "ba", "bahia": "ba",
    "pr": "pr", "paraná": "pr", "parana": "pr",
    "rs": "rs", "rio grande do sul": "rs",
    "go": "go", "goiás": "go", "goias": "go",
    "pe": "pe", "pernambuco": "pe",
    "ce": "ce", "ceará": "ce", "ceara": "ce",
    "sc": "sc", "santa catarina": "sc",
    "df": "df", "distrito federal": "df", "brasília": "df",
    "es": "es", "espírito santo": "es",
    "am": "am", "amazonas": "am",
    "pa": "pa", "pará": "pa",
    "ma": "ma", "maranhão": "ma",
    "ms": "ms", "mato grosso do sul": "ms",
    "mt": "mt", "mato grosso": "mt",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}


def _norm(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower().strip()


class OLXService:
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=25.0, headers=HEADERS, follow_redirects=True
        )

    async def search(self, criteria: SearchRequest) -> list[CarListing]:
        for attempt in range(2):
            try:
                state_slug = self._resolve_state(criteria.location)
                url = f"{OLX_BASE}/autos-e-pecas/carros-vans-e-utilitarios"
                if state_slug:
                    url += f"/estado-{state_slug}"

                params = {"q": criteria.model, "sf": "1", "o": "1"}
                resp = await self.client.get(url, params=params)

                if resp.status_code == 403:
                    logger.warning("OLX bloqueou a requisição (403)")
                    return []

                if resp.status_code != 200:
                    logger.warning(f"OLX retornou {resp.status_code}")
                    if attempt == 0:
                        await asyncio.sleep(1)
                        continue
                    return []

                return self._parse_html(resp.text, criteria)

            except httpx.TimeoutException:
                logger.warning(f"OLX timeout (tentativa {attempt+1})")
                if attempt == 0:
                    await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"Erro OLX: {e}")
                break
        return []

    def _parse_html(self, html: str, criteria: SearchRequest) -> list[CarListing]:
        listings: list[CarListing] = []
        try:
            match = re.search(
                r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
                html, re.DOTALL
            )
            if not match:
                logger.warning("OLX: __NEXT_DATA__ não encontrado")
                return []

            data = json.loads(match.group(1))
            # Navega na estrutura do Next.js da OLX
            page_props = data.get("props", {}).get("pageProps", {})

            # Tenta múltiplos caminhos para os anúncios
            ads: list[dict] = (
                page_props.get("ads")
                or page_props.get("listing", {}).get("props", {}).get("listingResponse", {}).get("ads")
                or []
            )

            for ad in ads[:30]:
                listing = self._parse_ad(ad, criteria)
                if listing:
                    listings.append(listing)

        except Exception as e:
            logger.error(f"Erro ao parsear OLX HTML: {e}")

        return listings

    def _parse_ad(self, ad: dict, criteria: SearchRequest) -> Optional[CarListing]:
        try:
            price_raw = ad.get("price", {})
            if isinstance(price_raw, dict):
                price = float(price_raw.get("value", 0))
            else:
                price = float(str(price_raw).replace("R$", "").replace(".", "").replace(",", ".").strip() or 0)

            if not price or price > criteria.max_price:
                return None

            title = ad.get("title") or ad.get("subject") or ""
            url = ad.get("url") or ad.get("listId") or ""
            if url and not url.startswith("http"):
                url = f"{OLX_BASE}{url}"

            location_raw = ad.get("location") or ad.get("address") or {}
            city = location_raw.get("city") or location_raw.get("neighbourhood", "")
            state = location_raw.get("state") or location_raw.get("uf", "")
            location_str = f"{city}/{state}".strip("/")

            # Extrai propriedades extras (ano, km)
            props = {p.get("name", "").lower(): p.get("value") for p in (ad.get("properties") or [])}
            year = self._safe_int(props.get("regdate") or props.get("ano"))
            km = self._safe_int(props.get("mileage") or props.get("km"))

            if criteria.max_km and km and km > criteria.max_km:
                return None
            if criteria.year_min and year and year < criteria.year_min:
                return None
            if criteria.year_max and year and year > criteria.year_max:
                return None

            images = ad.get("images") or ad.get("thumbnail") or []
            image_url = images[0].get("original") if isinstance(images, list) and images else None

            return CarListing(
                source="OLX",
                title=title,
                model=criteria.model,
                year=year,
                price=price,
                km=km,
                transmission=props.get("gearbox") or props.get("cambio"),
                fuel=props.get("fuel") or props.get("combustivel"),
                location=location_str,
                url=url,
                image_url=image_url,
                seller_type="loja" if ad.get("professionalAd") else "particular",
            )
        except Exception as e:
            logger.warning(f"Erro parse OLX ad: {e}")
            return None

    def _resolve_state(self, location: str) -> Optional[str]:
        loc = _norm(location)
        # Verifica sigla primeiro (ex: "SP", "/SP")
        for key, slug in STATE_SLUGS.items():
            if key in loc:
                return slug
        return None

    def _safe_int(self, value) -> Optional[int]:
        try:
            return int(str(value).replace(".", "").replace(",", "").strip())
        except (ValueError, TypeError):
            return None

    async def close(self):
        await self.client.aclose()
