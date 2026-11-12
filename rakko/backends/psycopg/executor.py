# Modified for Rakko ORM: port package imports and internal references to the rakko namespace.

from __future__ import annotations

from pypika_tortoise import Parameter

from rakko.backends.base_postgres.executor import BasePostgresExecutor


class PsycopgExecutor(BasePostgresExecutor):
    def parameter(self, pos: int) -> Parameter:
        return Parameter("%s")
