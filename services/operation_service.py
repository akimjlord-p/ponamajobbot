from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from db.models import WorkerPerformedOperation, Product, OperationType
from repositories.operation_repository import OperationRepository
from services.rate_service import RateService
from utils.apptime import apptime


class NormalizedOperation:
    def __init__(self, product: Product, operation: OperationType, quantity: int) -> None:
        self.product = product
        self.operation = operation
        self.quantity = quantity



class OperationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.operation_repository = OperationRepository(session)
        self.rate_service = RateService(session)

    async def create_performed_operation(
        self,
        product_id: int,
        operation_type_id: int,
        quantity: int,
        worker_id: int,
        session_id: int,
        report_id: int,
    ) -> WorkerPerformedOperation | None:
        product = await self.operation_repository.get_product_by_id(product_id)
        operation_type = await self.operation_repository.get_operation_type_by_id(operation_type_id)

        if not product or not operation_type:
            return None

        rate = await self.rate_service.get_rate(product_id, operation_type_id)
        if rate is None:
            return None

        quantity_decimal = Decimal(quantity)
        amount = rate.rate * quantity_decimal

        performed_operation = await self.operation_repository.create_operation(
            worker_id=worker_id,
            product_id=product_id,
            operation_id=operation_type_id,
            created_at=apptime(),
            session_id=session_id,
            report_id=report_id,
            operation_name_raw=operation_type.name,
            product_name_raw=product.name,
            rate_applied=rate.rate,
            rate_id=rate.id,
            amount=amount,
            quantity=quantity_decimal,
        )

        return performed_operation


class OperationNormalizerService:
    def __init__(self, session: AsyncSession):
        self.operation_repository = OperationRepository(session)

    async def normalize_operation(self, product_name: str, operation_name: str, quantity: int) -> NormalizedOperation | None:
        product = await self.operation_repository.get_product_by_name(product_name)
        if not product:
            product = await self.operation_repository.get_product_by_synonym(product_name)
        operation = await self.operation_repository.get_operation_type_by_name(operation_name)
        if not operation:
            operation = await self.operation_repository.get_operation_type_by_synonym(operation_name)

        if not operation or not product:
            return None

        return NormalizedOperation(product, operation, quantity)

