# Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
# Derived from Tortoise ORM; maintained and modified for Rakko ORM.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

from rakko.backends.base_postgres.schema_generator import BasePostgresSchemaGenerator

if TYPE_CHECKING:  # pragma: nocoverage
    from rakko.backends.psycopg.client import PsycopgClient


class PsycopgSchemaGenerator(BasePostgresSchemaGenerator):
    def __init__(self, client: PsycopgClient) -> None:
        super().__init__(client)
