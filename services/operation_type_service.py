from sqlalchemy.ext.asyncio import AsyncSession

from repositories.operation_repository import OperationRepository
from db.models import OperationType, OperationSynonym

class OperationTypeService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.operation_repository = OperationRepository(self.session)


    async def get_all_operation_types(self) -> list[OperationType] | None:
        operation_types = await self.operation_repository.get_operation_types()
        return operation_types

    async def add_operation_type(self, operation_name: str) -> OperationType | None:
        operation_type = self.operation_repository.get_operation_type_by_name(operation_name)
        if operation_type:
            return None
        new_operation_type = await self.operation_repository.create_operation_type(operation_name)
        await self.session.commit()
        return new_operation_type


    async def add_operation_type_synonyms(self, operation_type: OperationType, raw_synonyms: list[str]) -> list[OperationSynonym]:
        synonyms: list[OperationSynonym] = []
        for raw_synonym in raw_synonyms:
            synonym = await self.operation_repository.add_operation_synonym(
                operation_type.id,
                raw_synonym
            )
            synonyms.append(synonym)
        return synonyms

