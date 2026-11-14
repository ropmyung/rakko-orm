.. Modified for Rakko ORM: document the Rakko model/query API, project identity and development workflow.

.. _examples:

Examples
========

Current examples use isolated SQLite, except for a MySQL SQL-only preview.
Run examples from the project root with Python 3.12 or later:

.. code-block:: console

   uv run -m examples.basic
   uv run -m examples.queries
   uv run -m examples.relations
   uv run -m examples.bulk_and_transactions
   uv run -m examples.constraints

``constraints.py`` demonstrates CHECK constraints, composite uniqueness, indexes
and conditional uniqueness. Its models show nested ``@meta`` declarations,
``Meta = MetaOption(...)`` and attribute assignment after ``Meta = MetaOption()``.
Conditional unique constraints require PostgreSQL or SQLite.

The MySQL example previews schema and query SQL without connecting to a server:

.. code-block:: console

   uv run --extra aiomysql -m examples.mysql_sql

.. toctree::
   :maxdepth: 2

   examples/basic
