from .llm_connection import LLMConnection
from .prompts import Prompts
from utils.logger import get_logger


logger = get_logger(__name__)


class AISynonymsGenerator:
    def __init__(self, llm_connection: LLMConnection):
        self.llm_connection = llm_connection

    async def generate(self, word: str) -> list[str] | None:
        logger.info("Synonyms generation requested: word=%s", word)
        prompt = Prompts.get_prompt_for_synonym(word)
        result = await self.llm_connection.ask_text(prompt)

        if not result:
            logger.warning("Synonyms generation failed: empty llm response")
            return None

        result = result.replace("\n", ",")
        synonyms = [item.strip() for item in result.split(",") if item.strip()]

        logger.info("Synonyms generated: count=%s", len(synonyms))
        return synonyms

