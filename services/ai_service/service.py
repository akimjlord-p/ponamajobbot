from .parsing import AIReportParser
from .llm_connection import LLMConnection
from .synonyms import AISynonymsGenerator


class AIService:
    def __init__(self, llm_connection: LLMConnection) -> None:
        self.llm_connection = llm_connection
        self.AISynonymsGenerator = AISynonymsGenerator(llm_connection=self.llm_connection)


    async def parse_report(self, parsing_context: str, text: str):
        ai_report_parser = AIReportParser(llm_connection=self.llm_connection, parsing_context=parsing_context)
        ai_report = await ai_report_parser.parse(text)
        return ai_report


    async def generate_synonyms(self, word: str):
        return await self.AISynonymsGenerator.generate(word)


