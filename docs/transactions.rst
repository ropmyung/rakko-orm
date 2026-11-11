.. Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
   Derived from Tortoise ORM; maintained and modified for Rakko ORM.
   SPDX-License-Identifier: Apache-2.0

Transactions
============

Use ``in_transaction`` for an explicit connection context:

.. code-block:: python

    from rakko.transactions import in_transaction

    async with in_transaction() as connection:
        guild = await Guild.create(name="Builders").using_db(connection)
        await Member.create(connection, name="Ada", guild=guild)

The context commits on success and rolls back on an exception. Connection
selection, pools and savepoints remain in the async backend layer. ``atomic``
is available as a transaction decorator.

Upserts receive their connection after the lookup criterion:

.. code-block:: python

    guild, created = await Guild.get_or_create(
        Guild.name == "Builders", connection, name="Builders"
    )

The nested create/retry path preserves transaction connections and retries the
same lookup after a uniqueness conflict. Tests cover SQLite rollback,
explicit connections and concurrent upserts.
