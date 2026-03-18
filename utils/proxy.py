import httpx
from config import PROXY_URL


http_client = httpx.AsyncClient(
    proxy=PROXY_URL,
    timeout=30
)
