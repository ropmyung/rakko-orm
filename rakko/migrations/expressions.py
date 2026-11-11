# Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
# Derived from Tortoise ORM; maintained and modified for Rakko ORM.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations


class RawSQLTerm:
    def __init__(self, sql: str) -> None:
        self.sql = sql

    def get_sql(self, _context=None, dialect: str | None = None) -> str:
        return self.sql
