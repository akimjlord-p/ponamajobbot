import logging
from datetime import date, timedelta

from aiogram import Bot
from aiogram.enums import ParseMode

from config import MAIN_ID
from db.session import SessionLocal
from repositories.report_repository import ReportRepository
from utils.enums import ReportStatus

logger = logging.getLogger(__name__)

_STATUS_LABELS = {
    ReportStatus.PARSED: "обработан",
    ReportStatus.SHOULD_BE_SENT_TO_ADMIN: "требует проверки",
    ReportStatus.SENT_TO_ADMIN: "отправлен админу",
    ReportStatus.REVIEWED_BY_ADMIN: "проверен",
}


def _format_report_block(report) -> str:
    worker_name = f"@{report.worker.username}" if report.worker else "?"
    work_date = report.session.work_date.strftime("%d.%m.%Y") if report.session else "?"
    text_preview = report.text[:250] + "…" if len(report.text) > 250 else report.text
    status_label = _STATUS_LABELS.get(report.status, report.status.value)
    amount_line = f"\n💰 Сумма: <b>{report.total_amount} ₽</b>" if report.total_amount else ""
    return (
        f"👤 <b>{worker_name}</b>  |  📅 {work_date}  |  {status_label}\n"
        f"📝 {text_preview}"
        f"{amount_line}\n"
    )


async def _send_chunked(bot: Bot, chat_id: int, parts: list[str]) -> None:
    """Отправляет список строк одним или несколькими сообщениями (лимит 4000 символов)."""
    chunk = ""
    for part in parts:
        if len(chunk) + len(part) > 4000:
            await bot.send_message(chat_id, chunk, parse_mode=ParseMode.HTML)
            chunk = part
        else:
            chunk += part
    if chunk:
        await bot.send_message(chat_id, chunk, parse_mode=ParseMode.HTML)


async def send_weekly_reports(bot: Bot) -> None:
    """Еженедельная рассылка отчётов на MAIN_ID (каждое воскресенье 10:00 МСК).

    Порядок:
      1. Отчёты, которые ИИ не смог обработать (SHOULD_BE_SENT_TO_ADMIN).
      2. Все остальные отчёты за прошедшие 7 дней.
    """
    date_from = date.today() - timedelta(days=7)
    date_to = date.today()
    week_label = f"{date_from.strftime('%d.%m')} – {date_to.strftime('%d.%m.%Y')}"

    async with SessionLocal() as session:
        repo = ReportRepository(session)
        reports = await repo.get_weekly_reports()

    if not reports:
        await bot.send_message(
            MAIN_ID,
            f"📭 <b>Еженедельная сводка</b> ({week_label})\n\nОтчётов за неделю нет.",
            parse_mode=ParseMode.HTML,
        )
        logger.info("Weekly reports: nothing to send, MAIN_ID=%s", MAIN_ID)
        return

    unresolved = [r for r in reports if r.status == ReportStatus.SHOULD_BE_SENT_TO_ADMIN]
    others = [r for r in reports if r.status != ReportStatus.SHOULD_BE_SENT_TO_ADMIN]

    parts: list[str] = [
        f"📋 <b>Еженедельная сводка</b> ({week_label})\n"
        f"Всего отчётов: <b>{len(reports)}</b>\n\n"
    ]

    if unresolved:
        parts.append(f"⚠️ <b>Не обработаны ИИ — {len(unresolved)} шт.:</b>\n\n")
        for r in unresolved:
            parts.append(_format_report_block(r) + "\n")

    if others:
        parts.append(f"✅ <b>Остальные отчёты — {len(others)} шт.:</b>\n\n")
        for r in others:
            parts.append(_format_report_block(r) + "\n")

    await _send_chunked(bot, MAIN_ID, parts)
    logger.info(
        "Weekly reports sent: total=%s unresolved=%s others=%s MAIN_ID=%s",
        len(reports), len(unresolved), len(others), MAIN_ID,
    )
