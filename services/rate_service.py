from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Rate
from repositories.operation_repository import OperationRepository

from repositories.rate_repository import RateRepository

from utils.apptime import appdate
from decimal import Decimal


class RateService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.rate_repository = RateRepository(session)
        self.operation_repository = OperationRepository(session)

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

    async def get_rates(self) -> list[Rate] | None:
        rates = await self.rate_repository.get_rates()
        if not rates:
            return None
        return rates

    async def update_rate(self, product_name, operation_name, new_rate_value) -> Rate | None:
        product = await self.operation_repository.get_product_by_name(product_name)
        if not product:
            return None
        operation = await self.operation_repository.get_operation_type_by_name(operation_name)
        if not operation:
            return None
        old_rate = await self.get_rate(product.id, operation.id)
        old_rate.rate = new_rate_value
        new_rate = await self.rate_repository.update(old_rate)
        return new_rate

    async def deactivate_rate(self, product_id: int, operation_type_id: int) -> Rate | None:
        rate = await self.rate_repository.get_rate(product_id, operation_type_id, appdate())
        if not rate:
            return None
        await self.rate_repository.deactivate(rate.id)
        await self.session.commit()
        return rate

