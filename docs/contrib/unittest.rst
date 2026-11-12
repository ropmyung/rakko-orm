.. Modified for Rakko ORM: document the Rakko model/query API, project identity and development workflow.

Testing helpers
===============

Use ``rakko.context.tortoise_test_context`` for isolated async test databases.
The current pytest suite uses in-memory SQLite and model modules from
``tests.testmodels``. ``rakko.contrib.test`` also retains unittest helpers and
``init_memory_sqlite`` for small scripts.

Run the current execution and typing tests with:

.. code-block:: console

    uv run --all-groups --extra asyncpg --extra psycopg pytest -q

Pyright regression tests validate model constructor parameters, inheritance,
nullable values and rejection of invalid query calls. See
:doc:`../CONTRIBUTING` for development commands.
