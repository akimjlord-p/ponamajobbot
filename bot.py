import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN, TG_PROXY_URL
from middlewares import UserExistsMiddleware, AdminMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from handlers import ai_chapter, product_chapter, admin_worker_chapter, operation_chapter, rates_chapter, start, worker_chapter
from aiogram.client.session.aiohttp import AiohttpSession
from db.session import create_db_and_tables


session = AiohttpSession(proxy=TG_PROXY_URL)
bot = Bot(token=BOT_TOKEN, session=session)
dp = Dispatcher()

dp.message.outer_middleware(UserExistsMiddleware())
dp.message.outer_middleware(AdminMiddleware())

dp.include_router(ai_chapter.router)
dp.include_router(worker_chapter.router)
dp.include_router(admin_worker_chapter.router)
dp.include_router(product_chapter.router)
dp.include_router(operation_chapter.router)
dp.include_router(rates_chapter.router)
dp.include_router(start.router)







async def main() -> None:
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    logging.info("Add jobs: send_weekly_reports, send_daily_reports.")
    #scheduler.add_job(send_daily_reports, trigger="cron", hour=21, minute=0, kwargs={"bot": bot})
    scheduler.start()
    await create_db_and_tables()
    await dp.start_polling(bot)