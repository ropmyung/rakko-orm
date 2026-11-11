.. Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
   Derived from Tortoise ORM; maintained and modified for Rakko ORM.
   SPDX-License-Identifier: Apache-2.0

Logging
=======

The retained logging objects are exposed from ``rakko.log``. Their runtime
logger names are currently ``tortoise`` and ``tortoise.db_client``; these names
are implementation compatibility details inside Rakko.

Configure them through Python's logging module when inspecting SQL or backend
behavior. The ``run_async(..., verbose=True)`` helper also enables verbose
logging for scripts. SQL rendering and parameter execution remain separate;
examples can call ``query.sql()`` to inspect placeholders without interpolating
application values into SQL.
