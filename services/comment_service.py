from sqlalchemy.ext.asyncio import AsyncSession

from utils.enums import WorkerCommentTag
from db.models import WorkerComment
from repositories.comment_repository import CommentRepository
from repositories.user_repository import UserRepository
from utils.apptime import apptime
from utils.logger import get_logger


logger = get_logger(__name__)

class CommentService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.comment_repository = CommentRepository(session)
        self.user_repository = UserRepository(session)

    async def create(self, telegram_id: int, comment_text: str, tag: WorkerCommentTag) -> WorkerComment | None:
        logger.info("Create comment requested: telegram_id=%s tag=%s", telegram_id, tag.value)
        user = await self.user_repository.get_by_telegram_id(telegram_id)
        if user is None:
            logger.warning("Create comment failed: user not found telegram_id=%s", telegram_id)
            return None
        comment = await self.comment_repository.create(user.id, tag, comment_text, apptime())
        await self.session.commit()
        logger.info("Comment created: comment_id=%s user_id=%s", comment.id, user.id)
        return comment

    async def get_today_comments(self) -> list[WorkerComment] | None:
        today = apptime().date()
        comments = await self.comment_repository.get_comment_by_date(today)
        if comments:
            logger.debug("Today comments loaded: count=%s", len(comments))
            return comments
        else:
            logger.debug("Today comments loaded: no comments")
            return None


