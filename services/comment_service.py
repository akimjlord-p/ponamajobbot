from sqlalchemy.ext.asyncio import AsyncSession

from utils.enums import WorkerCommentTag
from db.models import WorkerComment
from repositories.comment_repository import CommentRepository
from repositories.user_repository import UserRepository
from utils.apptime import apptime

class CommentService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.comment_repository = CommentRepository(session)
        self.user_repository = UserRepository(session)

    async def create(self, telegram_id: int, comment_text: str, tag: WorkerCommentTag) -> WorkerComment | None:
        user = await self.user_repository.get_by_telegram_id(telegram_id)
        if user is None:
            return None
        comment = await self.comment_repository.create(user.id, tag, comment_text, apptime())
        await self.session.commit()
        return comment

    async def get_today_comments(self) -> list[WorkerComment] | None:
        today = apptime().date()
        comments = await self.comment_repository.get_comment_by_date(today)
        if comments:
            return comments
        else:
            return None


