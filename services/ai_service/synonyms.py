from .llm_connection import LLMConnection
from .prompts import Prompts


class AISynonymsGenerator:
    def __init__(self, llm_connection: LLMConnection):
        self.llm_connection = llm_connection

    async def generate(self, word: str) -> list[str] | None:
        prompt = Prompts.get_prompt_for_synonym(word)
        result = await self.llm_connection.ask_text(prompt)

        if not result:
            return None

        result = result.replace("\n", ",")
        synonyms = [item.strip() for item in result.split(",") if item.strip()]

        if not synonyms:
            return None

        return synonyms

