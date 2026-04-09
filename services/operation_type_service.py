from sqlalchemy.ext.asyncio import AsyncSession

from repositories.operation_repository import OperationRepository
from db.models import OperationType, OperationSynonym
from utils.logger import get_logger


logger = get_logger(__name__)

class OperationTypeService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.operation_repository = OperationRepository(self.session)

    async def get_all_operation_types(self) -> list[OperationType] | None:
        operation_types = await self.operation_repository.get_operation_types()
        logger.debug("Operation types loaded: count=%s", len(operation_types))
        return operation_types

    async def add_operation_type(self, operation_name: str) -> OperationType | None:
        logger.info("Add operation type requested: name=%s", operation_name)
        operation_type = await self.operation_repository.get_operation_type_by_name(operation_name)
        if operation_type:
            logger.warning("Add operation type skipped: already exists name=%s", operation_name)
            return None
        new_operation_type = await self.operation_repository.create_operation_type(operation_name)
        await self.session.commit()
        logger.info("Operation type created: id=%s name=%s", new_operation_type.id, operation_name)
        return new_operation_type

    async def get_operation_type_by_name(self, operation_name: str) -> OperationType | None:
        return await self.operation_repository.get_operation_type_by_name(operation_name)

    async def add_operation_type_synonyms(self, operation_type: OperationType, raw_synonyms: list[str]) -> list[OperationSynonym]:
        existing_synonyms = await self.operation_repository.get_operation_synonyms(operation_type.id)
        existing_values = {synonym.synonym.casefold() for synonym in existing_synonyms}
        existing_values.add(operation_type.name.casefold())

        prepared_synonyms: list[str] = []
        seen_values: set[str] = set()

        for raw_synonym in raw_synonyms:
            synonym_value = raw_synonym.strip()
            synonym_key = synonym_value.casefold()
            if not synonym_value:
                continue
            if synonym_key in existing_values or synonym_key in seen_values:
                continue
            seen_values.add(synonym_key)
            prepared_synonyms.append(synonym_value)

        synonyms: list[OperationSynonym] = []
        for raw_synonym in prepared_synonyms:
            synonym = await self.operation_repository.add_operation_synonym(
                operation_type.id,
                raw_synonym
            )
            synonyms.append(synonym)
        await self.session.commit()
        logger.info(
            "Operation synonyms added: operation_id=%s count=%s",
            operation_type.id,
            len(synonyms),
        )
        return synonyms

