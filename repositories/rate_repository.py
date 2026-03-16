from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Rate


class RateRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, rate_id: int) -> Rate | None:
        stmt = select(Rate).where(Rate.id == rate_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_rates(self) -> list[Rate]:
        stmt = (
            select(Rate)
            .where(Rate.is_active.is_(True))
            .order_by(Rate.valid_from.desc(), Rate.id.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_rates(
        self,
        *,
        operation_id: int | None = None,
        product_id: int | None = None,
        is_active: bool | None = None,
    ) -> list[Rate]:
        stmt = select(Rate)
        if operation_id is not None:
            stmt = stmt.where(Rate.operation_id == operation_id)
        if product_id is not None:
            stmt = stmt.where(Rate.product_id == product_id)
        if is_active is not None:
            stmt = stmt.where(Rate.is_active.is_(is_active))

        stmt = stmt.order_by(Rate.valid_from.desc(), Rate.id.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_rate(
        self,
        operation_id: int,
        product_id: int,
        target_date: date,
    ) -> Rate | None:
        stmt = (
            select(Rate)
            .where(
                Rate.operation_id == operation_id,
                Rate.product_id == product_id,
                Rate.is_active.is_(True),
                Rate.valid_from <= target_date,
                or_(Rate.valid_to.is_(None), Rate.valid_to >= target_date),
            )
            .order_by(Rate.valid_from.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create(
        self,
        operation_id: int,
        product_id: int,
        rate: Decimal,
        valid_from: date,
        valid_to: date | None = None,
        is_active: bool = True,
    ) -> Rate:
        rate_obj = Rate(
            operation_id=operation_id,
            product_id=product_id,
            rate=rate,
            valid_from=valid_from,
            valid_to=valid_to,
            is_active=is_active,
        )
        self.session.add(rate_obj)
        await self.session.flush()
        return rate_obj

    async def update(
        self,
        rate_obj: Rate,
        *,
        rate: Decimal | None = None,
        valid_from: date | None = None,
        valid_to: date | None = None,
        is_active: bool | None = None,
    ) -> Rate:
        if rate is not None:
            rate_obj.rate = rate
        if valid_from is not None:
            rate_obj.valid_from = valid_from
        if valid_to is not None:
            rate_obj.valid_to = valid_to
        if is_active is not None:
            rate_obj.is_active = is_active

        await self.session.flush()
        return rate_obj

    async def deactivate(self, rate_id: int) -> Rate | None:
        rate_obj = await self.get_by_id(rate_id)
        if rate_obj is None:
            return None

        rate_obj.is_active = False
        await self.session.flush()
        return rate_obj
