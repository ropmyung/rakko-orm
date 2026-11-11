# Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
# Derived from Tortoise ORM; maintained and modified for Rakko ORM.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

from rakko.backends.odbc.executor import ODBCExecutor
from rakko.exceptions import UnSupportedError


class MSSQLExecutor(ODBCExecutor):
    async def execute_explain(
        self, sql: str, output_fmt: str | None = None, **options: bool
    ) -> Any:
        raise UnSupportedError("MSSQL does not support explain")
