from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Product, ProductSynonym
from repositories.operation_repository import OperationRepository


class ProductService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.operation_repository = OperationRepository(self.session)

    async def get_all_product_names(self) -> list[str]:
        products = await self.operation_repository.get_products()
        return [product.name for product in products]

    async def get_product_by_name(self, product_name: str) -> Product | None:
        return await self.operation_repository.get_product_by_name(product_name)

    async def create_product(self, product_name: str) -> Product | None:
        if await self.operation_repository.get_product_by_name(product_name):
            return None
        product = await self.operation_repository.create_product(product_name)
        await self.session.commit()
        return product

    async def add_synonyms(self, product: Product, raw__synonyms: list[str]) -> list[ProductSynonym]:
        existing_synonyms = await self.operation_repository.get_product_synonyms(product.id)
        existing_values = {synonym.synonym.casefold() for synonym in existing_synonyms}
        existing_values.add(product.name.casefold())

        prepared_synonyms: list[str] = []
        seen_values: set[str] = set()

        for raw_synonym in raw__synonyms:
            synonym_value = raw_synonym.strip()
            synonym_key = synonym_value.casefold()
            if not synonym_value:
                continue
            if synonym_key in existing_values or synonym_key in seen_values:
                continue
            seen_values.add(synonym_key)
            prepared_synonyms.append(synonym_value)

        synonyms: list[ProductSynonym] = []
        for raw_synonym in prepared_synonyms:
            synonym = await self.operation_repository.add_product_synonym(
                product.id,
                raw_synonym)

            synonyms.append(synonym)
        await self.session.commit()
        return synonyms
