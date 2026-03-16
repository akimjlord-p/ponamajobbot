from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Rate

from repositories.rate_repository import RateRepository

from utils.apptime import appdate
from decimal import Decimal


class RateService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.rate_repository = RateRepository(session)

    async def get_rate(self, product_id: int, operation_type_id: int) -> Rate | None:
        rate = await self.rate_repository.get_rate(product_id, operation_type_id, appdate())
        return rate


    async def create_rate(self, product_id: int, operation_type_id: int, _rate: int) -> Rate | None:
        rate = await self.rate_repository.get_rate(product_id, operation_type_id, appdate())
        if rate:
            return None
        _rate = Decimal(_rate)
        rate = await self.rate_repository.create(product_id, operation_type_id, _rate, appdate())
        await self.session.commit()
        return rate


    async def deactivate_rate(self, product_id: int, operation_type_id: int) -> Rate | None:
        rate = await self.rate_repository.get_rate(product_id, operation_type_id, appdate())
        if not rate:
            return None
        await self.rate_repository.deactivate(rate.id)
        await self.session.commit()
        return rate

