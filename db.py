from sqlalchemy.orm import sessionmaker
from models import Base, WorkerBase, ReportBase, WorkSession, WeekReportBase  # noqa: F401
from sqlalchemy import create_engine, select
from models import Base
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


DB_URL = 'sqlite:///database.db'
engine = create_engine(DB_URL, echo=True)

def create_db_and_tables() -> None:
    Base.metadata.create_all(engine)


Session = sessionmaker(bind=engine)

# ==================================
#      workers
# ==================================
def add_worker_to_db(user: WorkerBase) -> None:
    with Session() as session:
        session.add(user)
        session.commit()


def get_worker_id_by_username(username: str) -> int | None:
    with Session() as session:
        statement = select(WorkerBase).where(WorkerBase.username == username)
        worker = session.scalars(statement).first()
        return worker.id if worker else None


def get_worker_id_by_telegram_id(telegram_id: int) -> int | None:
    with Session() as session:
        statement = select(WorkerBase).where(WorkerBase.telegram_id == telegram_id)
        worker = session.scalars(statement).first()
        return worker.id if worker else None


def get_all_usernames() -> list[str] | None:
    with Session() as session:
        statement = select(WorkerBase.username)
        return list(session.scalars(statement).all())


# ==================================
#      reports
# ==================================


def add_report_to_db(report: ReportBase) -> None:
    with Session() as session:
        session.add(report)
        session.commit()


def get_report_by_username(username: str) -> list[ReportBase]:
    with Session() as session:
        today_start = datetime.now(ZoneInfo("Europe/Moscow")).replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = datetime.now(ZoneInfo("Europe/Moscow")).replace(hour=23, minute=59, second=59, microsecond=999999)

        statement = (
            select(ReportBase)
            .join(WorkerBase)
            .where(
                WorkerBase.username == username,
                ReportBase.date >= today_start,
                ReportBase.date <= today_end
            )
        )
        return list(session.scalars(statement).all())


# ==================================
#      work_sessions
# ==================================


def get_today_session(worker_id: int) -> WorkSession | None:
    with Session() as session:
        today_start = datetime.now(ZoneInfo("Europe/Moscow")).replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = datetime.now(ZoneInfo("Europe/Moscow")).replace(hour=23, minute=59, second=59, microsecond=999999)

        statement = select(WorkSession).where(
            WorkSession.worker_id == worker_id,
            WorkSession.check_in >= today_start,
            WorkSession.check_in <= today_end
        )
        return session.scalars(statement).first()


def start_work_session(work_session: WorkSession) -> bool:
    with Session() as session:
        existing = get_today_session(work_session.worker_id)
        if existing:
            return False

        session.add(work_session)
        session.commit()
        return True


def get_open_session(worker_id: int) -> WorkSession | None:
    with Session() as session:
        statement = select(WorkSession).where(
            WorkSession.worker_id == worker_id,
            WorkSession.check_out.is_(None)
        )
        return session.scalars(statement).first()


def close_work_session(worker_id: int, checkout_time: datetime, report_id: int | None = None,
                       is_auto: bool = False) -> bool:
    with Session() as session:
        statement = select(WorkSession).where(
            WorkSession.worker_id == worker_id,
            WorkSession.check_out.is_(None)
        )
        work_session = session.scalars(statement).first()

        if not work_session:
            return False

        work_session.check_out = checkout_time
        work_session.report_id = report_id
        work_session.is_auto_checkout = is_auto
        session.commit()
        return True


# ==================================
#      week_reports
# ==================================


def add_week_report(week_report: WeekReportBase) -> bool:
    with Session() as session:
        statement = select(WeekReportBase).where(
            WeekReportBase.worker_id == week_report.worker_id,
            WeekReportBase.week_start_date == week_report.week_start_date,
            WeekReportBase.week_end_date == week_report.week_end_date
        )
        existing = session.scalars(statement).first()

        if existing:
            return False

        session.add(week_report)
        session.commit()
        return True


def get_week_report_by_username(username: str) -> WeekReportBase | None:
    with Session() as session:
        today = datetime.now(ZoneInfo("Europe/Moscow"))
        week_start = today - timedelta(days=today.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

        week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)

        statement = (
            select(WeekReportBase)
            .join(WorkerBase)
            .where(
                WorkerBase.username == username,
                WeekReportBase.week_start_date == week_start.date(),
                WeekReportBase.week_end_date == week_end.date()
            )
        )
        return session.scalars(statement).first()


