import logging
from aiogram import Bot, Dispatcher
from aiogram.types import Update
from config import MAIN_ID, BOT_TOKEN
from middlewares import AccessMiddleware, AdminMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from handlers import admin, start, report
from auto_mailings import send_weekly_reports, send_daily_reports


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.message.outer_middleware(AccessMiddleware())
dp.message.outer_middleware(AdminMiddleware())
dp.include_router(report.router)
dp.include_router(start.router)
dp.include_router(admin.router)






async def main() -> None:
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    logging.info("Add jobs: send_weekly_reports, send_daily_reports.")
    scheduler.add_job(send_weekly_reports, trigger="cron", day_of_week="sun", hour=9, minute=20, kwargs={"bot": bot})
    scheduler.add_job(send_daily_reports, trigger="cron", hour=21, minute=0, kwargs={"bot": bot})
    scheduler.start()
    await dp.start_polling(bot)