from datetime import date

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
        stmt = select(Rate).where(Rate.is_active.is_(True))
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
        rate,
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