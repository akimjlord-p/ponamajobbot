import logging
from aiogram import Bot, Dispatcher
from aiogram.types import Update
from config import MAIN_ID, BOT_TOKEN
from middlewares import AccessMiddleware, AdminMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from keyboards import get_kb
from handlers import admin, start, report

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.message.outer_middleware(AccessMiddleware())
dp.message.outer_middleware(AdminMiddleware())
dp.include_router(report.router)
dp.include_router(start.router)
dp.include_router(admin.router)


async def send_weekly_report(bot: Bot) -> None:
    report_text = """репорт"""
    await bot.send_message(chat_id=MAIN_ID, text=report_text, reply_markup=get_kb(is_admin=True))
    logging.info("Report sent")



async def main() -> None:
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

    scheduler.add_job(send_weekly_report, trigger="cron", day_of_week="sun", hour=9, minute=0, kwargs={"bot": bot})

    scheduler.start()
    await dp.start_polling(bot)