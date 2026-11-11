.. Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
   Derived from Tortoise ORM; maintained and modified for Rakko ORM.
   SPDX-License-Identifier: Apache-2.0

Schema creation
===============

``await context.generate_schemas()`` creates schema objects after model
registration. This is used for disposable SQLite examples and tests.

For a SQL-only preview:

.. code-block:: python

    client = context.db()
    sql = client.schema_generator(client).get_create_schema_sql()

This renders SQL without executing it. The MySQL example demonstrates unsigned
automatic IDs alongside an ordinary unsigned integer. Python ``default`` and
database ``db_default`` have separate responsibilities. See :doc:`migration`
for the adaptation status of persistent schema tooling.
