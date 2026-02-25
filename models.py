from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String


class Base(DeclarativeBase):
    pass


class WorkerBase(Base):
    __tablename__ = "workers"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)

    reports: Mapped[list["ReportBase"]] = relationship(back_populates="worker")

class ReportBase(Base):
    __tablename__ = "reports"
    id: Mapped[int] = mapped_column(primary_key=True)
    message: Mapped[str] = mapped_column(String())
    worker_id: Mapped[str] = mapped_column(ForeignKey("workers.id"))

    worker: Mapped["WorkerBase"] = relationship(back_populates="reports")


