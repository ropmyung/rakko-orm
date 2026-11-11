# Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
# Derived from Tortoise ORM; maintained and modified for Rakko ORM.
# SPDX-License-Identifier: Apache-2.0

"""Migration API (experimental).

Integration note: the migration API initializes apps without eagerly creating
database clients by calling ``Tortoise.init(..., init_connections=False)``.
Connections are created lazily when the executor requests them.
"""

from rakko.migrations.api.migrate import migrate
from rakko.migrations.api.plan import plan
from rakko.migrations.api.sqlmigrate import sqlmigrate

__all__ = ["migrate", "plan", "sqlmigrate"]
