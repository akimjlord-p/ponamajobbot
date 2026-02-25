import logging
from aiogram import Bot, Dispatcher
from aiogram.types import Update
from config import MAIN_ID, BOT_TOKEN
from middlewares import AccessMiddleware, AdminMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from keyboards import get_kb
from handlers import admin, start, report
from db import get_all_usernames, get_reports_by_username


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.message.outer_middleware(AccessMiddleware())
dp.message.outer_middleware(AdminMiddleware())
dp.include_router(report.router)
dp.include_router(start.router)
dp.include_router(admin.router)


async def send_weekly_report(bot: Bot) -> None:

    report_text = """Отчеты за последнюю неделю:\n"""
    all_users = []
    usernames = get_all_usernames()
    for username in usernames:
        reports = get_reports_by_username(username)
        res_reports = []
        for report in reports:
            res_reports.append(f"Дата: {report.date} \n" + str(report.message))
        all_users.append(f"Работник {username}" + '\n'.join(res_reports))
    report_text += "\n".join(all_users)
    await bot.send_message(chat_id=MAIN_ID, text=report_text, reply_markup=get_kb(is_admin=True))
    logging.info("Report sent")



async def main() -> None:
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

    scheduler.add_job(send_weekly_report, trigger="cron", day_of_week="wed", hour=21, minute=6, kwargs={"bot": bot})

    scheduler.start()
    await dp.start_polling(bot)