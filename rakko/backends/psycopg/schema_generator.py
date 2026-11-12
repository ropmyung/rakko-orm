# Modified for Rakko ORM: port package imports and internal references to the rakko namespace.

from __future__ import annotations

from typing import TYPE_CHECKING

from rakko.backends.base_postgres.schema_generator import BasePostgresSchemaGenerator

if TYPE_CHECKING:  # pragma: nocoverage
    from rakko.backends.psycopg.client import PsycopgClient


class PsycopgSchemaGenerator(BasePostgresSchemaGenerator):
    def __init__(self, client: PsycopgClient) -> None:
        super().__init__(client)
