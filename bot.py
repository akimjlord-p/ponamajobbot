import logging
from aiogram import Bot, Dispatcher
from aiogram.types import Update
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler

ADMIN_ID=os.environ.get("ADMIN_ID")
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


async def send_weekly_report(bot: Bot):
    report_text = """репорт"""
    await bot.send_message(chat_id=ADMIN_ID, text=report_text)
    logging.info("Report sent")



async def main():
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

    scheduler.add_job(send_weekly_report, trigger="croc", day_of_week="sun", hour=9, minute=0, kwargs={"bot": bot})

    scheduler.start()
    await dp.start_polling()