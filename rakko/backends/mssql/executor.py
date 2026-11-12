# Modified for Rakko ORM: port package imports and internal references to the rakko namespace.

from __future__ import annotations

from typing import Any

from rakko.backends.odbc.executor import ODBCExecutor
from rakko.exceptions import UnSupportedError


class MSSQLExecutor(ODBCExecutor):
    async def execute_explain(
        self, sql: str, output_fmt: str | None = None, **options: bool
    ) -> Any:
        raise UnSupportedError("MSSQL does not support explain")
