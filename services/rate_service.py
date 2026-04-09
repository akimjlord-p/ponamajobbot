from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Rate
from repositories.operation_repository import OperationRepository

from repositories.rate_repository import RateRepository

from utils.apptime import appdate
from utils.logger import get_logger
from decimal import Decimal


logger = get_logger(__name__)


class RateService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.rate_repository = RateRepository(session)
        self.operation_repository = OperationRepository(session)

    async def get_rate(self, product_id: int, operation_type_id: int) -> Rate | None:
        rate = await self.rate_repository.get_rate(product_id, operation_type_id, appdate())
        if rate is None:
            logger.debug(
                "Rate not found: product_id=%s operation_type_id=%s",
                product_id,
                operation_type_id,
            )
        return rate


    async def create_rate(self, product_id: int, operation_type_id: int, _rate: int) -> Rate | None:
        logger.info(
            "Create rate requested: product_id=%s operation_type_id=%s rate=%s",
            product_id,
            operation_type_id,
            _rate,
        )
        rate = await self.rate_repository.get_rate(product_id, operation_type_id, appdate())
        if rate:
            logger.warning(
                "Create rate skipped: active rate already exists product_id=%s operation_type_id=%s",
                product_id,
                operation_type_id,
            )
            return None
        _rate = Decimal(_rate)
        rate = await self.rate_repository.create(product_id, operation_type_id, _rate, appdate())
        await self.session.commit()
        logger.info("Rate created: rate_id=%s", rate.id)
        return rate

    async def get_rates(self) -> list[Rate] | None:
        rates = await self.rate_repository.get_rates()
        if not rates:
            logger.debug("Rates list loaded: empty")
            return None
        logger.debug("Rates list loaded: count=%s", len(rates))
        return rates

    async def update_rate(self, product_name: str, operation_type_name: str, new_rate_value: Decimal) -> Rate | None:
        logger.info(
            "Update rate requested: product=%s operation=%s new_rate=%s",
            product_name,
            operation_type_name,
            new_rate_value,
        )
        product = await self.operation_repository.get_product_by_name(product_name)
        if not product:
            logger.warning("Update rate failed: product not found name=%s", product_name)
            return None
        operation_type = await self.operation_repository.get_operation_type_by_name(operation_type_name)
        if not operation_type:
            logger.warning("Update rate failed: operation type not found name=%s", operation_type_name)
            return None
        old_rate = await self.get_rate(product.id, operation_type.id)
        if not old_rate:
            logger.warning("Update rate failed: active rate not found")
            return None
        old_rate.rate = new_rate_value
        new_rate = await self.rate_repository.update(old_rate)
        await self.session.commit()
        logger.info("Rate updated: rate_id=%s", new_rate.id)
        return new_rate

    async def deactivate_rate(self, product_name: str, operation_type_name: str) -> Rate | None:
        logger.info("Deactivate rate requested: product=%s operation=%s", product_name, operation_type_name)
        product = await self.operation_repository.get_product_by_name(product_name)
        if not product:
            logger.warning("Deactivate rate failed: product not found name=%s", product_name)
            return None
        operation_type = await self.operation_repository.get_operation_type_by_name(operation_type_name)
        if not operation_type:
            logger.warning("Deactivate rate failed: operation type not found name=%s", operation_type_name)
            return None
        rate = await self.rate_repository.get_rate(product.id, operation_type.id, appdate())
        if not rate:
            logger.warning("Deactivate rate failed: active rate not found")
            return None
        rate = await self.rate_repository.deactivate(rate.id)
        await self.session.commit()
        logger.info("Rate deactivated: rate_id=%s", rate.id)
        return rate

