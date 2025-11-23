import httpx
from bs4 import BeautifulSoup
import re
from tenacity import retry, stop_after_attempt, wait_exponential
from logger import logger
from settings import settings
from time import time

_cache = {}
_CACHE_TTL = 60 * 60  

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
async def extract_abstract_from_url(url: str) -> str:
    if not url:
        return ""
    cached = _cache_get(url)
    if cached is not None:
        return cached

    headers = {'User-Agent': 'Mozilla/5.0 (compatible; ScientificAnalyzer/1.0)'}
    try:
        async with httpx.AsyncClient(timeout=settings.web_timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                return ""
            text = resp.text
    except Exception as e:
        logger.debug(f"Failed to fetch {url}: {e}")
        return ""

    try:
        soup = BeautifulSoup(text, 'html.parser')

     
        selectors = [
            ("section", {"class": re.compile("abstract", re.I)}),
            ("div", {"class": re.compile("abstract", re.I)}),
            ("div", {"id": re.compile("abstract", re.I)}),
            ("section", {"id": re.compile("abstract", re.I)}),
            ("div", {"class": re.compile("article__abstract", re.I)}),
            ("div", {"class": re.compile("article-section__content", re.I)}),
        ]
        for tag, attrs in selectors:
            el = soup.find(tag, attrs=attrs)
            if el:
                p = el.find('p') or el
                text_content = p.get_text(separator=" ", strip=True)
                if text_content and len(text_content) > 50:
                    _cache_set(url, text_content)
                    return text_content

    
        meta = soup.find('meta', attrs={'name': re.compile('description', re.I)}) \
               or soup.find('meta', attrs={'property': re.compile('og:description', re.I)})
        if meta:
            content = meta.get('content', '').strip()
            if content and len(content) > 50:
                _cache_set(url, content)
                return content

        main = soup.find('main') or soup.find('article') or soup
        for p in main.find_all('p'):
            txt = p.get_text(separator=" ", strip=True)
            if txt and len(txt) > 80:
                _cache_set(url, txt)
                return txt

    except Exception as e:
        logger.debug(f"Failed to parse HTML {url}: {e}")

    return ""

