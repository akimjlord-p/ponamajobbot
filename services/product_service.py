from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Product, ProductSynonym
from repositories.operation_repository import OperationRepository


class ProductService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.operation_repository = OperationRepository(self.session)


    async def create_product(self, product_name: str) -> Product | None:
        if await self.operation_repository.get_product_by_name(product_name):
            return None
        product = await self.operation_repository.create_product(product_name)
        await self.session.commit()
        return product

    async def add_synonyms(self, product: Product, raw__synonyms: list[str]) -> list[ProductSynonym]:
        synonyms: list[ProductSynonym] = []
        for raw_synonym in raw__synonyms:
            synonym = await self.operation_repository.add_product_synonym(
                product.id,
                raw_synonym)

            synonyms.append(synonym)
        await self.session.commit()
        return synonyms
