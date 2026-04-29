from .llm_connection import LLMConnection
from .service import AIService
from utils.proxy import http_client, web_search_http_client
from utils.logger import get_logger


logger = get_logger(__name__)

llm_mini = LLMConnection(
    model="gpt-4.1-mini",
    http_client=http_client,
    web_search_enabled=False,
)

llm_smart = LLMConnection(
    model="gpt-4.1",
    http_client=http_client,
    web_search_enabled=True,
    web_search_http_client=web_search_http_client,
)

ai_service_mini = AIService(llm_mini)
ai_service_smart = AIService(llm_smart)

logger.info("AI service container initialized")

