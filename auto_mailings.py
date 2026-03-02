from db import get_all_usernames, get_today_session, get_worker_id_by_username, get_report_by_username, \
    get_week_report_by_username
from datetime import datetime
from zoneinfo import ZoneInfo
from config import MAIN_ID
import logging
from aiogram import Bot
from keyboards import get_kb

async def send_weekly_reports(bot: Bot) -> None:

    report_text = """Недельные отчеты:\n"""
    usernames = get_all_usernames()
    for username in usernames:
        week_report = get_week_report_by_username(username)
        if week_report:
            report_text += f"\nОтчет сотрудника {username}\n{week_report.message}"
        else:
            report_text += f"\nСотрудник {username} не отправил отчет"
    await bot.send_message(chat_id=MAIN_ID, text=report_text, reply_markup=get_kb(is_admin=True), parse_mode="HTML")
    logging.info("Weekly reports sent")


async def   send_daily_reports(bot: Bot) -> None:
    now = datetime.now(ZoneInfo("Europe/Moscow")).strftime("%d.%m")
    report_text = f"Отчеты сотрудников за {now}"
    usernames = get_all_usernames()
    for username in usernames:
        session = get_today_session(get_worker_id_by_username(username=username))
        if session:
            duration = session.check_out - session.check_in

            total_seconds = int(duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            report = get_report_by_username(username)
            if not report:
                report = "Сотрудник не отправил отчет"
            else:
                report = report[0].message
            report_text += "\n" + "\n" + f"Сотрудник <b>{username}</b>" + "\n" + f"Время работы: {hours}ч {minutes}м" + "\n" + f"Отчёт: {report}"

    await bot.send_message(chat_id=MAIN_ID, text=report_text, parse_mode="HTML", reply_markup=get_kb(is_admin=True))


