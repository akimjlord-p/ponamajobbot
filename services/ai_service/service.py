from sqlalchemy.ext.asyncio import AsyncSession

from db.models import AdminRequestsContext
from .parsing import AIReportParser
from .llm_connection import LLMConnection
from .synonyms import AISynonymsGenerator
from .analytics import AIAnalytics
from .external_research import ExternalResearchService
from utils.logger import get_logger


logger = get_logger(__name__)

class AIService:
    def __init__(
        self,
        llm_connection: LLMConnection,
        external_research_service: ExternalResearchService | None = None,
    ) -> None:
        self.llm_connection = llm_connection
        self.external_research_service = external_research_service
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
        if (
            response
            and response.needs_external_data
            and self.external_research_service is not None
            and self._should_run_external_research(question, response.research_brief)
        ):
            external_answer = await self.external_research_service.research(
                question=question,
                research_brief=response.research_brief or "",
            )
            if external_answer:
                response.answer = external_answer
            else:
                response.answer = (
                    "Нужны внешние данные, но внешний поиск сейчас недоступен.\n"
                    f"Что нужно проверить: {response.research_brief or 'не указано'}"
                )
        return response

    @staticmethod
    def _should_run_external_research(question: str, research_brief: str | None) -> bool:
        text = f"{question}\n{research_brief or ''}".lower()
        markers = [
            "конкурент",
            "рынок",
            "тренд",
            "бенчмарк",
            "отрасл",
            "ниша",
            "внешн",
            "сравни с",
            "сравнение с",
        ]
        return any(marker in text for marker in markers)


