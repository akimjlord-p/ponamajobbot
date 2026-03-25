from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from db.models import AdminParsingContext, AdminRequestsContext
from repositories.ai_repository import AiRepository
from utils.apptime import apptime


class ContextService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.ai_repository = AiRepository(session)

    async def add_parsing_context(self, text: str, created_by_admin_id: int) -> AdminParsingContext:
        context = await self.ai_repository.create_parsing_context(
            text=text,
            created_by_admin_id=created_by_admin_id,
            created_at=apptime(),
        )
        await self.session.commit()
        return context

    async def add_admin_requests_context(
        self,
        text: str,
        created_by_admin_id: int,
    ) -> AdminRequestsContext:
        context = await self.ai_repository.create_requests_context(
            text=text,
            created_by_admin_id=created_by_admin_id,
            created_at=apptime(),
        )
        await self.session.commit()
        return context

    async def get_admin_requests_contexts(self) -> list[AdminRequestsContext]:
        return await self.ai_repository.get_active_requests_contexts()

    async def get_parsing_contexts(self) -> list[AdminParsingContext]:
        return await self.ai_repository.get_active_parsing_contexts()
