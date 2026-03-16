from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import (
    WorkerPerformedOperation,
    OperationType,
    OperationSynonym,
    Product,
    ProductSynonym,
)


class OperationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_operations_by_report(self, report_id: int) -> list[WorkerPerformedOperation]:
        stmt = (
            select(WorkerPerformedOperation)
            .where(WorkerPerformedOperation.report_id == report_id)
            .order_by(WorkerPerformedOperation.id.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_worker_operations(self, worker_id: int) -> list[WorkerPerformedOperation]:
        stmt = (
            select(WorkerPerformedOperation)
            .where(WorkerPerformedOperation.worker_id == worker_id)
            .order_by(WorkerPerformedOperation.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_by_report(self, report_id: int) -> None:
        stmt = delete(WorkerPerformedOperation).where(
            WorkerPerformedOperation.report_id == report_id
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def create_operation(
        self,
        worker_id: int,
        report_id: int,
        quantity: Decimal,
        created_at,
        session_id: int | None = None,
        operation_id: int | None = None,
        product_id: int | None = None,
        rate_id: int | None = None,
        operation_name_raw: str | None = None,
        product_name_raw: str | None = None,
        rate_applied: Decimal | None = None,
        amount: Decimal | None = None,
    ) -> WorkerPerformedOperation:
        operation = WorkerPerformedOperation(
            worker_id=worker_id,
            report_id=report_id,
            session_id=session_id,
            operation_id=operation_id,
            product_id=product_id,
            rate_id=rate_id,
            operation_name_raw=operation_name_raw,
            product_name_raw=product_name_raw,
            quantity=quantity,
            rate_applied=rate_applied,
            amount=amount,
            created_at=created_at,
        )
        self.session.add(operation)
        await self.session.flush()
        return operation

    async def get_operation_type_by_name(self, name: str) -> OperationType | None:
        stmt = select(OperationType).where(OperationType.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_operation_type_by_synonym(self, synonym: str) -> OperationType | None:
        stmt = (
            select(OperationType)
            .join(OperationSynonym, OperationSynonym.operation_id == OperationType.id)
            .where(OperationSynonym.synonym == synonym)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_product_by_name(self, name: str) -> Product | None:
        stmt = select(Product).where(Product.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_product_by_synonym(self, synonym: str) -> Product | None:
        stmt = (
            select(Product)
            .join(ProductSynonym, ProductSynonym.product_id == Product.id)
            .where(ProductSynonym.synonym == synonym)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()