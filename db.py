from sqlalchemy.orm import sessionmaker, selectinload
from models import Base, WorkerBase, ReportBase  # noqa: F401
from sqlalchemy import create_engine, select, delete
from models import Base


DB_URL = 'sqlite:///db/database.db'
engine = create_engine(DB_URL, echo=True)

def create_db_and_tables() -> None:
    Base.metadata.create_all(engine)


Session = sessionmaker(bind=engine)


def add_worker_to_db(user: WorkerBase) -> None:
    with Session() as session:
        session.add(user)
        session.commit()


def get_worker_id_by_username(username: str) -> int | None:
    with Session() as session:
        statement = select(WorkerBase).where(WorkerBase.username == username)
        worker = session.scalars(statement).first()
        return worker.id if worker else None


def add_report_to_db(report: ReportBase) -> None:
    with Session() as session:
        session.add(report)
        session.commit()


def get_report_by_username(username: str) -> list[ReportBase]:
    with Session() as session:
        statement = select(WorkerBase).where(WorkerBase.username == username).options(selectinload(WorkerBase.reports))
        worker = session.scalars(statement).first()
        return worker.reports if worker else []


def clear_all_reports() -> None:
    with Session() as session:
        statement = delete(ReportBase)
        session.execute(statement)
        session.commit()


