import httpx
from langchain_openai import ChatOpenAI

from config import OPENAI_API_KEY


class LLMConnection:
    def __init__(self, model: str, http_client: httpx.AsyncClient) -> None:
        self.llm = ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model=model,
            http_client=http_client,
            temperature=0,
        )

    async def ask_text(self, prompt: str) -> str | None:
        try:
            response = await self.llm.ainvoke(prompt)
            return str(response.content).strip()
        except Exception as ex:
            return None