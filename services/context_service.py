from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from db.models import AdminParsingContext, AdminRequestsContext
from repositories.ai_repository import AiRepository
from utils.apptime import apptime
from utils.logger import get_logger


logger = get_logger(__name__)


class ContextService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.ai_repository = AiRepository(session)

    async def add_parsing_context(self, text: str, created_by_admin_id: int) -> AdminParsingContext:
        logger.info("Add parsing context requested: admin_id=%s", created_by_admin_id)
        context = await self.ai_repository.create_parsing_context(
            text=text,
            created_by_admin_id=created_by_admin_id,
            created_at=apptime(),
        )
        await self.session.commit()
        logger.info("Parsing context created: context_id=%s", context.id)
        return context

    async def add_admin_requests_context(
        self,
        text: str,
        created_by_admin_id: int,
    ) -> AdminRequestsContext:
        logger.info("Add admin request context requested: admin_id=%s", created_by_admin_id)
        context = await self.ai_repository.create_requests_context(
            text=text,
            created_by_admin_id=created_by_admin_id,
            created_at=apptime(),
        )
        await self.session.commit()
        logger.info("Admin request context created: context_id=%s", context.id)
        return context

    async def get_admin_requests_contexts(self) -> list[AdminRequestsContext]:
        contexts = await self.ai_repository.get_active_requests_contexts()
        logger.debug("Active admin request contexts loaded: count=%s", len(contexts))
        return contexts

    async def get_parsing_contexts(self) -> list[AdminParsingContext]:
        contexts = await self.ai_repository.get_active_parsing_contexts()
        logger.debug("Active parsing contexts loaded: count=%s", len(contexts))
        return contexts
