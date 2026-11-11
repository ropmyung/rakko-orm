# Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
# Derived from Tortoise ORM; maintained and modified for Rakko ORM.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass

from rakko.models import Model


@dataclass
class ModelSqlData:
    table: str
    model: type[Model]
    table_sql: str
    references: set[str]
    m2m_tables_sql: list[str]
