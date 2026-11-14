# Modified for Rakko ORM: port package imports and internal references to the rakko namespace.

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

import asyncpg

from rakko import Model
from rakko.backends.base_postgres.executor import BasePostgresExecutor


class AsyncpgExecutor(BasePostgresExecutor):
    async def _process_insert_result(
        self, instance: Model, results: asyncpg.Record | Mapping[str, Any] | None
    ) -> None:
        return await super()._process_insert_result(
            instance, cast(Mapping[str, Any] | None, results)
        )
