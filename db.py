from sqlalchemy.orm import sessionmaker
from models import Base, UserBase, ReportBase # noqa: F401
from sqlalchemy import create_engine, select, delete
from models import Base

DB_URL = 'sqlite:///db/database.db'
engine = create_engine(DB_URL, echo=True)

def create_db_and_tables() -> None:
    Base.metadata.create_all(engine)


Session = sessionmaker(bind=engine)


def add_user_to_db(user: UserBase) -> None:
    with Session() as session:
        session.add(user)
        session.commit()


def get_user_by_username(username: str) -> UserBase:
    with Session() as session:
        statement = select(UserBase).where(UserBase.username == username)
        return session.scalars(statement).one()


def add_report_to_db(report: ReportBase) -> None:
    with Session() as session:
        session.add(report)
        session.commit()


def get_report_by_username(user_id: int) -> ReportBase:
    with Session() as session:
        statement = select(ReportBase).where(ReportBase.user_id == user_id)
        return session.scalars(statement).one()


