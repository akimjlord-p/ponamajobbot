from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String
from datetime import datetime

class Base(DeclarativeBase):
    pass


class WorkerBase(Base):
    __tablename__ = "workers"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    telegram_id: Mapped[int | None] = mapped_column(unique=True, nullable=True)

    reports: Mapped[list["ReportBase"]] = relationship(back_populates="worker")
    sessions: Mapped[list["WorkSession"]] = relationship(back_populates="worker")
    week_reports: Mapped[list["WeekReportBase"]] = relationship(back_populates="worker")# ДОБАВИЛ


class WorkSession(Base):
    __tablename__ = "work_sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    worker_id: Mapped[int] = mapped_column(ForeignKey("workers.id"))

    check_in: Mapped[datetime] = mapped_column()
    check_out: Mapped[datetime | None] = mapped_column(nullable=True)
    is_auto_checkout: Mapped[bool] = mapped_column(default=False)

    report_id: Mapped[int | None] = mapped_column(ForeignKey("reports.id"), nullable=True)

    worker: Mapped["WorkerBase"] = relationship(back_populates="sessions")
    report: Mapped["ReportBase"] = relationship(back_populates="session")


class ReportBase(Base):
    __tablename__ = "reports"
    id: Mapped[int] = mapped_column(primary_key=True)
    message: Mapped[str] = mapped_column(String())
    date: Mapped[datetime] = mapped_column()
    worker_id: Mapped[int] = mapped_column(ForeignKey("workers.id"))

    worker: Mapped["WorkerBase"] = relationship(back_populates="reports")
    session: Mapped["WorkSession"] = relationship(back_populates="report", uselist=False)


class WeekReportBase(Base):
    __tablename__ = "week_reports"
    id: Mapped[int] = mapped_column(primary_key=True)
    message: Mapped[str] = mapped_column(String())
    week_start_date: Mapped[datetime] = mapped_column()
    week_end_date: Mapped[datetime] = mapped_column()
    worker_id: Mapped[int] = mapped_column(ForeignKey("workers.id"))

    worker: Mapped["WorkerBase"] = relationship(back_populates="week_reports")


