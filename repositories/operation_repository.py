from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import (
    OperationType,
    OperationSynonym,
    Product,
    ProductSynonym,
    WorkerPerformedOperation,
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

    async def get_by_id(self, operation_entry_id: int) -> WorkerPerformedOperation | None:
        stmt = select(WorkerPerformedOperation).where(
            WorkerPerformedOperation.id == operation_entry_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

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
        created_at: datetime,
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

    async def update_operation(
        self,
        operation: WorkerPerformedOperation,
        *,
        worker_id: int | None = None,
        report_id: int | None = None,
        session_id: int | None = None,
        operation_id: int | None = None,
        product_id: int | None = None,
        rate_id: int | None = None,
        operation_name_raw: str | None = None,
        product_name_raw: str | None = None,
        quantity: Decimal | None = None,
        rate_applied: Decimal | None = None,
        amount: Decimal | None = None,
    ) -> WorkerPerformedOperation:
        if worker_id is not None:
            operation.worker_id = worker_id
        if report_id is not None:
            operation.report_id = report_id
        if session_id is not None:
            operation.session_id = session_id
        if operation_id is not None:
            operation.operation_id = operation_id
        if product_id is not None:
            operation.product_id = product_id
        if rate_id is not None:
            operation.rate_id = rate_id
        if operation_name_raw is not None:
            operation.operation_name_raw = operation_name_raw
        if product_name_raw is not None:
            operation.product_name_raw = product_name_raw
        if quantity is not None:
            operation.quantity = quantity
        if rate_applied is not None:
            operation.rate_applied = rate_applied
        if amount is not None:
            operation.amount = amount

        await self.session.flush()
        return operation

    async def delete_operation(self, operation: WorkerPerformedOperation) -> None:
        await self.session.delete(operation)
        await self.session.flush()

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

    async def get_operation_type_by_id(self, operation_id: int) -> OperationType | None:
        stmt = select(OperationType).where(OperationType.id == operation_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_operation_types(self, *, is_active: bool | None = None) -> list[OperationType]:
        stmt = select(OperationType).options(selectinload(OperationType.synonyms))
        if is_active is not None:
            stmt = stmt.where(OperationType.is_active.is_(is_active))
        stmt = stmt.order_by(OperationType.name.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_operation_type(
        self,
        name: str,
        *,
        is_active: bool = True,
    ) -> OperationType:
        operation_type = OperationType(name=name, is_active=is_active)
        self.session.add(operation_type)
        await self.session.flush()
        return operation_type

    async def update_operation_type(
        self,
        operation_type: OperationType,
        *,
        name: str | None = None,
        is_active: bool | None = None,
    ) -> OperationType:
        if name is not None:
            operation_type.name = name
        if is_active is not None:
            operation_type.is_active = is_active

        await self.session.flush()
        return operation_type

    async def add_operation_synonym(
        self,
        operation_id: int,
        synonym: str,
    ) -> OperationSynonym:
        operation_synonym = OperationSynonym(
            operation_id=operation_id,
            synonym=synonym,
        )
        self.session.add(operation_synonym)
        await self.session.flush()
        return operation_synonym

    async def get_operation_synonyms(self, operation_id: int) -> list[OperationSynonym]:
        stmt = (
            select(OperationSynonym)
            .where(OperationSynonym.operation_id == operation_id)
            .order_by(OperationSynonym.synonym.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_operation_synonym(self, synonym_id: int) -> bool:
        synonym = await self.session.get(OperationSynonym, synonym_id)
        if synonym is None:
            return False

        await self.session.delete(synonym)
        await self.session.flush()
        return True

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

    async def get_product_by_id(self, product_id: int) -> Product | None:
        stmt = select(Product).where(Product.id == product_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_products(self, *, is_active: bool | None = None) -> list[Product]:
        stmt = select(Product).options(selectinload(Product.synonyms))
        if is_active is not None:
            stmt = stmt.where(Product.is_active.is_(is_active))
        stmt = stmt.order_by(Product.name.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_product(
        self,
        name: str,
        *,
        is_active: bool = True,
    ) -> Product:
        product = Product(name=name, is_active=is_active)
        self.session.add(product)
        await self.session.flush()
        return product

    async def update_product(
        self,
        product: Product,
        *,
        name: str | None = None,
        is_active: bool | None = None,
    ) -> Product:
        if name is not None:
            product.name = name
        if is_active is not None:
            product.is_active = is_active

        await self.session.flush()
        return product

    async def add_product_synonym(
        self,
        product_id: int,
        synonym: str,
    ) -> ProductSynonym:
        product_synonym = ProductSynonym(
            product_id=product_id,
            synonym=synonym,
        )
        self.session.add(product_synonym)
        await self.session.flush()
        return product_synonym

    async def get_product_synonyms(self, product_id: int) -> list[ProductSynonym]:
        stmt = (
            select(ProductSynonym)
            .where(ProductSynonym.product_id == product_id)
            .order_by(ProductSynonym.synonym.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_product_synonym(self, synonym_id: int) -> bool:
        synonym = await self.session.get(ProductSynonym, synonym_id)
        if synonym is None:
            return False

        await self.session.delete(synonym)
        await self.session.flush()
        return True
