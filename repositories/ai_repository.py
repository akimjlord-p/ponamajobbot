from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import AdminAiRequest, AdminParsingContext, AdminRequestsContext


class AiRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_ai_request(
        self,
        admin_user_id: int,
        question: str,
        created_at: datetime,
        report_id: int | None = None,
        context_id: int | None = None,
        answer: str | None = None,
    ) -> AdminAiRequest:
        ai_request = AdminAiRequest(
            admin_user_id=admin_user_id,
            report_id=report_id,
            context_id=context_id,
            question=question,
            answer=answer,
            created_at=created_at,
        )
        self.session.add(ai_request)
        await self.session.flush()
        return ai_request

    async def set_answer(
        self,
        request_id: int,
        answer: str,
    ) -> AdminAiRequest | None:
        ai_request = await self.get_ai_request_by_id(request_id)
        if not ai_request:
            return None

        ai_request.answer = answer
        await self.session.flush()
        return ai_request

    async def get_ai_request_by_id(self, request_id: int) -> AdminAiRequest | None:
        stmt = select(AdminAiRequest).where(AdminAiRequest.id == request_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_ai_requests(self) -> list[AdminAiRequest]:
        stmt = select(AdminAiRequest).order_by(AdminAiRequest.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_ai_requests_by_report(self, report_id: int) -> list[AdminAiRequest]:
        stmt = (
            select(AdminAiRequest)
            .where(AdminAiRequest.report_id == report_id)
            .order_by(AdminAiRequest.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_parsing_context(
        self,
        text: str,
        created_by_admin_id: int,
        created_at: datetime,
        is_active: bool = True,
    ) -> AdminParsingContext:
        context = AdminParsingContext(
            text=text,
            is_active=is_active,
            created_by_admin_id=created_by_admin_id,
            created_at=created_at,
        )
        self.session.add(context)
        await self.session.flush()
        return context

    async def get_active_parsing_contexts(self) -> list[AdminParsingContext]:
        stmt = (
            select(AdminParsingContext)
            .where(AdminParsingContext.is_active.is_(True))
            .order_by(AdminParsingContext.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def deactivate_parsing_contexts(self) -> None:
        contexts = await self.get_active_parsing_contexts()
        for context in contexts:
            context.is_active = False
        await self.session.flush()

    async def create_requests_context(
        self,
        text: str,
        created_by_admin_id: int,
        created_at: datetime,
        is_active: bool = True,
    ) -> AdminRequestsContext:
        context = AdminRequestsContext(
            text=text,
            is_active=is_active,
            created_by_admin_id=created_by_admin_id,
            created_at=created_at,
        )
        self.session.add(context)
        await self.session.flush()
        return context

    async def get_active_requests_contexts(self) -> list[AdminRequestsContext]:
        stmt = (
            select(AdminRequestsContext)
            .where(AdminRequestsContext.is_active.is_(True))
            .order_by(AdminRequestsContext.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def deactivate_requests_contexts(self) -> None:
        contexts = await self.get_active_requests_contexts()
        for context in contexts:
            context.is_active = False
        await self.session.flush()
