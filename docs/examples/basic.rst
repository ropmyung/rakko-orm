.. Modified for Rakko ORM: document the Rakko model/query API, project identity and development workflow.

.. _examples_simple:

Runnable examples
=================

Run these examples from the project root. Each SQLite example creates its own
in-memory database and closes its connections when it finishes.

.. code-block:: console

    uv run -m examples.basic
    uv run -m examples.queries
    uv run -m examples.relations
    uv run -m examples.bulk_and_transactions

.. _example_basic:

Basic CRUD and metadata
-----------------------

This example declares typed fields and metadata, creates records, performs a
partial update and deletes matching records using model-bound criteria.

.. literalinclude:: ../../examples/basic.py
   :language: python

Shared models
-------------

The following examples reuse these models. The reverse relation is declared
as a descriptor and is excluded from model constructor parameters.

.. literalinclude:: ../../examples/models.py
   :language: python

Field-based queries
-------------------

Conditions, ordering, projections, grouping and partial models use class-level
field references. Named projections can contain arithmetic and aggregate
expressions. Nullable Text and JSON fields can be omitted during creation.

.. literalinclude:: ../../examples/queries.py
   :language: python

.. _example_relations:

Relations and prefetching
-------------------------

Use foreign-key fields for filtering and eager loading. Reverse descriptors
can be passed directly to prefetch operations, including filtered prefetches.

.. literalinclude:: ../../examples/relations.py
   :language: python

.. _example_transactions:

Bulk operations and transactions
--------------------------------

Field references are accepted in bulk update lists, conflict targets and
instance update mappings. Upserts accept typed model constructor arguments.
Queries can select the active transaction connection.

.. literalinclude:: ../../examples/bulk_and_transactions.py
   :language: python

MySQL SQL preview
-----------------

The MySQL example renders schema, SELECT and UPDATE SQL without opening a
database connection. It demonstrates UNSIGNED integers and AUTO_INCREMENT.
Install the optional MySQL driver when running it:

.. code-block:: console

    uv run --extra aiomysql -m examples.mysql_sql

.. literalinclude:: ../../examples/mysql_sql.py
   :language: python

Validation
----------

The test suite runs the SQLite scripts and verifies that the MySQL preview
does not open a connection:

.. code-block:: console

    uv run --group test pytest tests/test_examples.py -q
