from .llm_connection import LLMConnection
from .service import AIService
from utils.proxy import http_client

llm_connection = LLMConnection(
    model="gpt-4.1-mini",
    http_client=http_client,
)

ai_service = AIService(llm_connection)