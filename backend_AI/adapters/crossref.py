# api/adapters/crossref.py
import httpx
import asyncio
from typing import List, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential
from time import time
from logger import logger
from settings import settings

# простой in-memory TTL cache
_cache = {}
_CACHE_TTL = 60 * 60  # 1 hour

def _cache_get(key):
    entry = _cache.get(key)
    if not entry:
        return None
    ts, value = entry
    if time() - ts > _CACHE_TTL:
        del _cache[key]
        return None
    return value

def _cache_set(key, value):
    _cache[key] = (time(), value)

@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=5))
async def search_papers_on_crossref(query: str, limit: int = 100) -> List[Dict[str, Any]]:
    key = f"crossref:{query}:{limit}"
    cached = _cache_get(key)
    if cached is not None:
        return cached

    params = {
        "query.bibliographic": query,
        "rows": limit,
        "sort": "relevance",
        "select": "title,URL,abstract,DOI"
    }

    async with httpx.AsyncClient(timeout=settings.crossref_timeout) as client:
        try:
            resp = await client.get("https://api.crossref.org/works", params=params)
            if resp.status_code == 200:
                items = resp.json().get("message", {}).get("items", [])
                _cache_set(key, items)
                return items
            else:
                logger.warning(f"Crossref returned status {resp.status_code} for query {query}")
        except Exception as e:
            logger.error(f"Crossref API error: {e}")
    return []
