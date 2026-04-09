import httpx
from langchain_openai import ChatOpenAI

from config import OPENAI_API_KEY
from utils.logger import get_logger


logger = get_logger(__name__)


class LLMConnection:
    def __init__(self, model: str, http_client: httpx.AsyncClient) -> None:
        self.model = model
        self.llm = ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model=model,
            http_client=http_client,
            temperature=0,
        )
        logger.info("LLM connection initialized: model=%s", model)

    async def ask_text(self, prompt: str) -> str | None:
        logger.debug("LLM request started: model=%s prompt_len=%s", self.model, len(prompt))
        try:
            response = await self.llm.ainvoke(prompt)
            logger.debug("LLM request completed: model=%s", self.model)
            return str(response.content).strip()
        except Exception as ex:
            logger.exception("LLM request failed: model=%s error=%s", self.model, ex)
            return None
