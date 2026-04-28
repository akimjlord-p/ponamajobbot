from .llm_connection import LLMConnection
from .service import AIService
from .external_research import ExternalResearchService
from config import ENABLE_ANALYTICS_WEB_SEARCH, ANALYTICS_WEB_SEARCH_MODEL
from utils.proxy import http_client
from utils.logger import get_logger


logger = get_logger(__name__)

llm_mini = LLMConnection(
    model="gpt-4.1-mini",
    http_client=http_client,
)

llm_smart = LLMConnection(
    model="gpt-4.1",
    http_client=http_client,
)

ai_service_mini = AIService(llm_mini)

analytics_external_research_service = (
    ExternalResearchService(model=ANALYTICS_WEB_SEARCH_MODEL)
    if ENABLE_ANALYTICS_WEB_SEARCH
    else None
)

ai_service_smart = AIService(
    llm_smart,
    external_research_service=analytics_external_research_service,
)

logger.info("AI service container initialized")

