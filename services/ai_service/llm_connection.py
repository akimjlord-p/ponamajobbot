import httpx
from openai import AsyncOpenAI
from langchain_openai import ChatOpenAI

from config import OPENAI_API_KEY
from utils.logger import get_logger


logger = get_logger(__name__)


class LLMConnection:
    def __init__(
        self,
        model: str,
        http_client: httpx.AsyncClient,
        web_search_enabled: bool = False,
        web_search_http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.model = model
        self.web_search_enabled = web_search_enabled
        self.openai_client = AsyncOpenAI(
            api_key=OPENAI_API_KEY,
            http_client=web_search_http_client or http_client,
        )
        self.llm = ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model=model,
            http_client=http_client,
            temperature=0,
        )
        logger.info("LLM connection initialized: model=%s web_search_enabled=%s", model, web_search_enabled)

    async def ask_text(self, prompt: str) -> str | None:
        logger.debug("LLM request started: model=%s prompt_len=%s", self.model, len(prompt))
        try:
            response = await self.llm.ainvoke(prompt)
            logger.debug("LLM request completed: model=%s", self.model)
            return str(response.content).strip()
        except Exception as ex:
            logger.exception("LLM request failed: model=%s error=%s", self.model, ex)
            return None

    async def ask_web_search(self, prompt: str) -> str | None:
        if not self.web_search_enabled:
            logger.info("LLM web search skipped: model=%s disabled", self.model)
            return None
        try:
            response = await self.openai_client.responses.create(
                model=self.model,
                tools=[{"type": "web_search"}],
                tool_choice="auto",
                input=prompt,
            )
            output_text = (getattr(response, "output_text", None) or "").strip()
            return output_text or None
        except Exception as ex:
            logger.exception("LLM web search failed: model=%s error=%s", self.model, ex)
            return None
