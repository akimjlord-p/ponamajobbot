from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import (
    String,
    Text,
    Boolean,
    DateTime,
    Date,
    ForeignKey,
    UniqueConstraint,
    Enum as SAEnum,
    Numeric,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base
from utils.enums import *


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    telegram_id: Mapped[int | None] = mapped_column(unique=True, nullable=True, index=True)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), nullable=False)
    authorised_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    work_sessions: Mapped[list["WorkSession"]] = relationship(
        back_populates="worker",
        foreign_keys="WorkSession.worker_id",
    )

    reports: Mapped[list["WorkReport"]] = relationship(
        back_populates="worker",
        foreign_keys="WorkReport.worker_id",
    )

    performed_operations: Mapped[list["WorkerPerformedOperation"]] = relationship(
        back_populates="worker"
    )

    comments: Mapped[list["WorkerComment"]] = relationship(
        back_populates="worker"
    )


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    synonyms: Mapped[list["ProductSynonym"]] = relationship(back_populates="product")


class ProductSynonym(Base):
    __tablename__ = "product_synonyms"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        nullable=False,
        index=True,
    )
    synonym: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    product: Mapped["Product"] = relationship(back_populates="synonyms")

    __table_args__ = (
        UniqueConstraint("product_id", "synonym", name="uq_product_synonym"),
    )


class OperationType(Base):
    __tablename__ = "operation_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    synonyms: Mapped[list["OperationSynonym"]] = relationship(back_populates="operation")


class OperationSynonym(Base):
    __tablename__ = "operation_synonyms"

    id: Mapped[int] = mapped_column(primary_key=True)
    operation_id: Mapped[int] = mapped_column(
        ForeignKey("operation_types.id"),
        nullable=False,
        index=True,
    )
    synonym: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    operation: Mapped["OperationType"] = relationship(back_populates="synonyms")

    __table_args__ = (
        UniqueConstraint("operation_id", "synonym", name="uq_operation_synonym"),
    )


class Rate(Base):
    __tablename__ = "rates"

    id: Mapped[int] = mapped_column(primary_key=True)

    operation_id: Mapped[int] = mapped_column(
        ForeignKey("operation_types.id"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        nullable=False,
        index=True,
    )

    rate: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "operation_id",
            "product_id",
            "valid_from",
            name="uq_rate_version",
        ),
    )


class AdminParsingContext(Base):
    __tablename__ = "admin_parsing_contexts"

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by_admin_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


class AdminRequestsContext(Base):
    __tablename__ = "admin_requests_contexts"

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by_admin_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


class WorkSession(Base):
    __tablename__ = "work_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)

    worker_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    created_by_admin_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    work_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    status: Mapped[SessionStatus] = mapped_column(
        SAEnum(SessionStatus),
        default=SessionStatus.OPEN,
        nullable=False,
    )

    is_auto_checkout: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_created_by_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    worker: Mapped["User"] = relationship(
        back_populates="work_sessions",
        foreign_keys=[worker_id],
    )

    report: Mapped["WorkReport | None"] = relationship(
        back_populates="session",
        uselist=False,
    )


class WorkReport(Base):
    __tablename__ = "work_reports"

    id: Mapped[int] = mapped_column(primary_key=True)

    session_id: Mapped[int] = mapped_column(
        ForeignKey("work_sessions.id"),
        unique=True,
        nullable=False,
        index=True,
    )
    worker_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    text: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[ReportStatus] = mapped_column(
        SAEnum(ReportStatus),
        nullable=False,
    )

    result_type: Mapped[ReportResultType | None] = mapped_column(
        SAEnum(ReportResultType),
        nullable=True,
    )

    admin_review_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by_admin_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    total_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    session: Mapped["WorkSession"] = relationship(back_populates="report")
    worker: Mapped["User"] = relationship(
        back_populates="reports",
        foreign_keys=[worker_id],
    )

    performed_operations: Mapped[list["WorkerPerformedOperation"]] = relationship(
        back_populates="report",
        cascade="all, delete-orphan",
    )


class WorkerPerformedOperation(Base):
    __tablename__ = "worker_performed_operations"

    id: Mapped[int] = mapped_column(primary_key=True)

    worker_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    report_id: Mapped[int] = mapped_column(
        ForeignKey("work_reports.id"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[int | None] = mapped_column(
        ForeignKey("work_sessions.id"),
        nullable=True,
        index=True,
    )

    operation_id: Mapped[int | None] = mapped_column(
        ForeignKey("operation_types.id"),
        nullable=True,
        index=True,
    )
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id"),
        nullable=True,
        index=True,
    )
    rate_id: Mapped[int | None] = mapped_column(
        ForeignKey("rates.id"),
        nullable=True,
        index=True,
    )

    operation_name_raw: Mapped[str | None] = mapped_column(String(255), nullable=True)
    product_name_raw: Mapped[str | None] = mapped_column(String(255), nullable=True)

    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    rate_applied: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    worker: Mapped["User"] = relationship(back_populates="performed_operations")
    report: Mapped["WorkReport"] = relationship(back_populates="performed_operations")


class WorkerComment(Base):
    __tablename__ = "worker_comments"

    id: Mapped[int] = mapped_column(primary_key=True)

    worker_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    report_id: Mapped[int | None] = mapped_column(
        ForeignKey("work_reports.id"),
        nullable=True,
        index=True,
    )

    tag: Mapped[WorkerCommentTag] = mapped_column(
        SAEnum(WorkerCommentTag),
        nullable=False,
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    worker: Mapped["User"] = relationship(back_populates="comments")


class AdminAiRequest(Base):
    __tablename__ = "admin_ai_requests"

    id: Mapped[int] = mapped_column(primary_key=True)

    admin_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    report_id: Mapped[int | None] = mapped_column(
        ForeignKey("work_reports.id"),
        nullable=True,
        index=True,
    )

    context_id: Mapped[int | None] = mapped_column(
        ForeignKey("admin_requests_contexts.id"),
        nullable=True,
        index=True,
    )

    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)