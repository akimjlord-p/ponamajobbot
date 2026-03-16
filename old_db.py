from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import and_, event, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from models import Base, ReportBase, WeekReportBase, WorkSession, WorkerBase


DB_URL = "sqlite+aiosqlite:///database.db"
engine = create_async_engine(
    DB_URL,
    echo=True,
    connect_args={"timeout": 30},
)


@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA busy_timeout=30000;")
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()


Session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def create_db_and_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ==================================
#      workers
# ==================================
async def add_worker_to_db(user: WorkerBase) -> None:
    async with Session() as session:
        session.add(user)
        await session.commit()


async def get_worker_id_by_username(username: str) -> int | None:
    async with Session() as session:
        statement = select(WorkerBase).where(WorkerBase.username == username)
        worker = (await session.scalars(statement)).first()
        return worker.id if worker else None


async def get_worker_id_by_telegram_id(telegram_id: int) -> int | None:
    async with Session() as session:
        statement = select(WorkerBase).where(WorkerBase.telegram_id == telegram_id)
        worker = (await session.scalars(statement)).first()
        return worker.id if worker else None


async def get_all_usernames() -> list[str]:
    async with Session() as session:
        statement = select(WorkerBase.username)
        return list((await session.scalars(statement)).all())


# ==================================
#      reports
# ==================================
async def add_report_to_db(report: ReportBase) -> None:
    async with Session() as session:
        session.add(report)
        await session.commit()
        await session.refresh(report)


async def get_report_by_username(username: str) -> list[ReportBase]:
    async with Session() as session:
        today_start = datetime.now(ZoneInfo("Europe/Moscow")).replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = datetime.now(ZoneInfo("Europe/Moscow")).replace(hour=23, minute=59, second=59, microsecond=999999)

        statement = (
            select(ReportBase)
            .join(WorkerBase)
            .where(
                WorkerBase.username == username,
                ReportBase.date >= today_start,
                ReportBase.date <= today_end,
            )
        )
        return list((await session.scalars(statement)).all())


# ==================================
#      work_sessions
# ==================================
async def get_today_session(worker_id: int) -> WorkSession | None:
    async with Session() as session:
        today_start = datetime.now(ZoneInfo("Europe/Moscow")).replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = datetime.now(ZoneInfo("Europe/Moscow")).replace(hour=23, minute=59, second=59, microsecond=999999)

        statement = select(WorkSession).where(
            WorkSession.worker_id == worker_id,
            WorkSession.check_in >= today_start,
            WorkSession.check_in <= today_end,
        )
        return (await session.scalars(statement)).first()


async def start_work_session(work_session: WorkSession) -> bool:
    async with Session() as session:
        today_start = datetime.now(ZoneInfo("Europe/Moscow")).replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = datetime.now(ZoneInfo("Europe/Moscow")).replace(hour=23, minute=59, second=59, microsecond=999999)

        statement = select(WorkSession).where(
            WorkSession.worker_id == work_session.worker_id,
            WorkSession.check_in >= today_start,
            WorkSession.check_in <= today_end,
        )
        existing = (await session.scalars(statement)).first()
        if existing:
            return False

        session.add(work_session)
        await session.commit()
        return True


async def get_open_session(worker_id: int) -> WorkSession | None:
    async with Session() as session:
        statement = select(WorkSession).where(
            WorkSession.worker_id == worker_id,
            WorkSession.check_out.is_(None),
        )
        return (await session.scalars(statement)).first()


async def close_work_session(
    worker_id: int,
    checkout_time: datetime,
    report_id: int | None = None,
    is_auto: bool = False,
) -> bool:
    async with Session() as session:
        statement = select(WorkSession).where(
            WorkSession.worker_id == worker_id,
            WorkSession.check_out.is_(None),
        )
        work_session = (await session.scalars(statement)).first()

        if not work_session:
            return False

        work_session.check_out = checkout_time
        work_session.report_id = report_id
        work_session.is_auto_checkout = is_auto
        await session.commit()
        return True


# ==================================
#      week_reports
# ==================================
async def add_week_report(week_report: WeekReportBase) -> bool:
    async with Session() as session:
        statement = select(WeekReportBase).where(
            WeekReportBase.worker_id == week_report.worker_id,
            WeekReportBase.week_start_date == week_report.week_start_date,
            WeekReportBase.week_end_date == week_report.week_end_date,
        )
        existing = (await session.scalars(statement)).first()

        if existing:
            return False

        session.add(week_report)
        await session.commit()
        return True


async def get_week_report_by_username(username: str) -> WeekReportBase | None:
    async with Session() as session:
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
                WeekReportBase.week_end_date == week_end.date(),
            )
        )
        return (await session.scalars(statement)).first()


async def get_weekly_report_snapshots() -> list[tuple[str, str | None]]:
    async with Session() as session:
        today = datetime.now(ZoneInfo("Europe/Moscow"))
        week_start = today - timedelta(days=today.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)

        statement = (
            select(WorkerBase.username, WeekReportBase.message)
            .outerjoin(
                WeekReportBase,
                and_(
                    WeekReportBase.worker_id == WorkerBase.id,
                    WeekReportBase.week_start_date == week_start.date(),
                    WeekReportBase.week_end_date == week_end.date(),
                ),
            )
            .order_by(WorkerBase.username)
        )
        rows = (await session.execute(statement)).all()
        return [(row[0], row[1]) for row in rows]


async def get_daily_report_snapshots() -> list[tuple[str, datetime | None, datetime | None, str | None]]:
    async with Session() as session:
        today_start = datetime.now(ZoneInfo("Europe/Moscow")).replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = datetime.now(ZoneInfo("Europe/Moscow")).replace(hour=23, minute=59, second=59, microsecond=999999)

        latest_report_subquery = (
            select(
                ReportBase.worker_id.label("worker_id"),
                ReportBase.message.label("message"),
                func.row_number()
                .over(partition_by=ReportBase.worker_id, order_by=ReportBase.date.desc())
                .label("rn"),
            )
            .where(
                ReportBase.date >= today_start,
                ReportBase.date <= today_end,
            )
            .subquery()
        )

        statement = (
            select(
                WorkerBase.username,
                WorkSession.check_in,
                WorkSession.check_out,
                latest_report_subquery.c.message,
            )
            .outerjoin(
                WorkSession,
                and_(
                    WorkSession.worker_id == WorkerBase.id,
                    WorkSession.check_in >= today_start,
                    WorkSession.check_in <= today_end,
                ),
            )
            .outerjoin(
                latest_report_subquery,
                and_(
                    latest_report_subquery.c.worker_id == WorkerBase.id,
                    latest_report_subquery.c.rn == 1,
                ),
            )
            .order_by(WorkerBase.username)
        )
        rows = (await session.execute(statement)).all()
        return [(row[0], row[1], row[2], row[3]) for row in rows]
