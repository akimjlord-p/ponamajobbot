from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.enums import WorkerCommentTag
from db.models import WorkerComment


class CommentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        worker_id: int,
        tag: WorkerCommentTag,
        text: str,
        created_at: datetime,
        report_id: int | None = None,
    ) -> WorkerComment:
        comment = WorkerComment(
            worker_id=worker_id,
            report_id=report_id,
            tag=tag,
            text=text,
            created_at=created_at,
        )
        self.session.add(comment)
        await self.session.flush()
        return comment

    async def get_by_id(self, comment_id: int) -> WorkerComment | None:
        stmt = select(WorkerComment).where(WorkerComment.id == comment_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_worker_comments(self, worker_id: int) -> list[WorkerComment]:
        stmt = (
            select(WorkerComment)
            .where(WorkerComment.worker_id == worker_id)
            .order_by(WorkerComment.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_comments_by_tag(self, tag: WorkerCommentTag) -> list[WorkerComment]:
        stmt = (
            select(WorkerComment)
            .where(WorkerComment.tag == tag)
            .order_by(WorkerComment.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_text(self, comment: WorkerComment, text: str) -> WorkerComment:
        comment.text = text
        await self.session.flush()
        return comment

    async def delete(self, comment: WorkerComment) -> None:
        await self.session.delete(comment)
        await self.session.flush()

    async def get_report_comments(self, report_id: int) -> list[WorkerComment]:
        stmt = (
            select(WorkerComment)
            .where(WorkerComment.report_id == report_id)
            .order_by(WorkerComment.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
