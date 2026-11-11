.. Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
   Derived from Tortoise ORM; maintained and modified for Rakko ORM.
   SPDX-License-Identifier: Apache-2.0

.. _databases:

Databases
=========

MySQL
-----

Install a MySQL driver extra and configure a URL:

.. code-block:: console

    uv sync --extra aiomysql

.. code-block:: python

    await context.init(
        db_url="mysql://user:password@localhost:3306/database",
        modules={"models": ["myapp.models"]},
    )

``asyncmy`` is an alternative extra. MySQL async access, pooling and transactions
are core requirements. Integer fields support ``unsigned=True``; automatic
factories render AUTO_INCREMENT explicitly.

Preview MySQL SQL without connecting to a server:

.. code-block:: console

    uv run --extra aiomysql -m examples.mysql_sql

SQLite and retained adapters
----------------------------

``aiosqlite`` is a core dependency. Examples use ``sqlite://:memory:``; a file
DB can use ``sqlite://db.sqlite3``. SQLite execution is covered by current tests.

PostgreSQL adapters use ``asyncpg``/``psycopg`` extras. MSSQL/Oracle ODBC adapters
remain in the backend tree. Their implementation is retained while the API
evolves. Current verification includes MySQL/PostgreSQL SQL generation rather
than a claimed live-server compatibility matrix for every backend.
