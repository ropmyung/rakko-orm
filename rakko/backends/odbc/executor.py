# Modified for Rakko ORM: port package imports and internal references to the rakko namespace.

from rakko import Model
from rakko.backends.base.executor import BaseExecutor
from rakko.fields import BigIntField, IntField, SmallIntField


class ODBCExecutor(BaseExecutor):
    async def _process_insert_result(self, instance: Model, results: int) -> None:
        pk_field_object = self.model._meta.pk
        if (
            isinstance(pk_field_object, (SmallIntField, IntField, BigIntField))
            and pk_field_object.generated
            and not instance._custom_generated_pk
        ):
            instance.pk = results
        if self.model._meta.db_default_db_columns:
            await self._fetch_db_defaults_after_insert(instance)
