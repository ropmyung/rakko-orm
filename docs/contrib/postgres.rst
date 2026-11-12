.. Modified for Rakko ORM: document the Rakko model/query API, project identity and development workflow.

PostgreSQL extensions
=====================

PostgreSQL adapters and extension types are retained in
``rakko.backends.asyncpg``, ``rakko.backends.psycopg`` and ``rakko.contrib.postgres``.
Backend-specific indexes, functions and fields remain distinct from the new
core model/criterion API.

SQL rendering is covered by focused tests; broader live-database validation is
planned. Use the ``asyncpg`` or ``psycopg`` extra for the selected driver and
configure model modules with Rakko declarations. See :doc:`../databases`.
