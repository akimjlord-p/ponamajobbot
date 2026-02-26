async def send_weekly_report(bot: Bot) -> None:

    report_text = """Отчеты за последнюю неделю:\n"""
    all_users = []
    usernames = get_all_usernames()
    for username in usernames:
        reports = get_reports_by_username(username)
        res_reports = []
        for report in reports:
            res_reports.append(f"---Дата: {report.date} \n" + str(report.message))
        all_users.append(f"Работник <b>{username}</b>" + "\n" + "\n".join(res_reports))
    report_text += "\n".join(all_users)
    await bot.send_message(chat_id=MAIN_ID, text=report_text, reply_markup=get_kb(is_admin=True), parse_mode="HTML")
    logging.info("Report sent")
    clear_all_reports()
    logging.info("All reports cleared")