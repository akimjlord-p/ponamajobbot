import httpx
from config import PROXY_URL, TG_PROXY_URL


http_client = httpx.AsyncClient(
    proxy=PROXY_URL,
    timeout=30
)

web_search_http_client = httpx.AsyncClient(
    proxy=TG_PROXY_URL,
    timeout=60,
)
