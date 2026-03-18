import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot

from config import MAIN_ID
from db import get_daily_report_snapshots, get_weekly_report_snapshots
from old_keyboards import get_kb


async def send_weekly_reports(bot: Bot) -> None:
    report_text = "Недельные отчеты:\n"
    rows = await get_weekly_report_snapshots()

    for username, week_message in rows:
        if week_message:
            report_text += f"\nОтчет сотрудника {username}\n{week_message}"
        else:
            report_text += f"\nСотрудник {username} не отправил отчет"

    await bot.send_message(
        chat_id=MAIN_ID,
        text=report_text,
        reply_markup=get_kb(is_admin=True),
        parse_mode="HTML",
    )
    logging.info("Weekly reports sent")


async def send_daily_reports(bot: Bot) -> None:
    now = datetime.now(ZoneInfo("Europe/Moscow")).strftime("%d.%m")
    report_text = f"Отчеты сотрудников за {now}"
    rows = await get_daily_report_snapshots()

    for username, check_in, check_out, report_message in rows:
        if not check_in or not check_out:
            continue

        duration = check_out - check_in
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        report = report_message or "Сотрудник не отправил отчет"

        report_text += (
            "\n\n"
            + f"Сотрудник <b>{username}</b>\n"
            + f"Время работы: {hours}ч {minutes}м\n"
            + f"Отчет: {report}"
        )

    await bot.send_message(
        chat_id=MAIN_ID,
        text=report_text,
        parse_mode="HTML",
        reply_markup=get_kb(is_admin=True),
    )
