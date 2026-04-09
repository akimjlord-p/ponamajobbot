from sqlalchemy.ext.asyncio import AsyncSession

from db.models import AdminRequestsContext
from .parsing import AIReportParser
from .llm_connection import LLMConnection
from .synonyms import AISynonymsGenerator
from .analytics import AIAnalytics
from utils.logger import get_logger


logger = get_logger(__name__)

class AIService:
    def __init__(self, llm_connection: LLMConnection) -> None:
        self.llm_connection = llm_connection
        self.AISynonymsGenerator = AISynonymsGenerator(llm_connection=self.llm_connection)
        logger.info("AIService initialized")


    async def parse_report(self, parsing_context: str, text: str):
        logger.debug("AIService.parse_report called")
        ai_report_parser = AIReportParser(llm_connection=self.llm_connection, parsing_context=parsing_context)
        ai_report = await ai_report_parser.parse(text)
        return ai_report


    async def generate_synonyms(self, word: str):
        logger.debug("AIService.generate_synonyms called: word=%s", word)
        return await self.AISynonymsGenerator.generate(word)

    async def analytic_question(self, question: str, session: AsyncSession, context: list[AdminRequestsContext]):
        logger.debug("AIService.analytic_question called: question_len=%s", len(question))
        ai_analytics = AIAnalytics(connection=self.llm_connection, session=session)
        response = await ai_analytics.question(question, context)
        return response


