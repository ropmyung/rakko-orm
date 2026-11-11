.. Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
   Derived from Tortoise ORM; maintained and modified for Rakko ORM.
   SPDX-License-Identifier: Apache-2.0

Configuration
=============

A context owns model registration, database clients and connection lifetime.
Import ``TortoiseContext`` from ``rakko.context``; this is a retained helper
name inside Rakko, not an import from a separately installed Tortoise package.

.. code-block:: python

    from rakko.context import TortoiseContext

    async with TortoiseContext() as context:
        await context.init(
            db_url="sqlite://:memory:",
            modules={"models": ["examples.models"]},
        )
        await context.generate_schemas()
        # Await model queries here.

Use schema generation for disposable examples/tests. Persistent schema changes
need a reviewed plan; see :doc:`migration`. Driver extras and MySQL URLs are
covered in :doc:`databases`.
