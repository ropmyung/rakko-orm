# Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
# Derived from Tortoise ORM; maintained and modified for Rakko ORM.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pypika_tortoise import Parameter

from rakko.backends.base_postgres.executor import BasePostgresExecutor


class PsycopgExecutor(BasePostgresExecutor):
    def parameter(self, pos: int) -> Parameter:
        return Parameter("%s")
