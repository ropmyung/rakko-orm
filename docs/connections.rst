.. Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
   Derived from Tortoise ORM; maintained and modified for Rakko ORM.
   SPDX-License-Identifier: Apache-2.0

Connections and contexts
========================

``rakko.context.TortoiseContext`` owns configuration, model registration and
connection cleanup. It retains an implementation name from the original
codebase while being provided by the independent ``rakko`` package.

.. code-block:: python

    async with TortoiseContext() as context:
        await context.init(
            db_url="sqlite://:memory:", modules={"models": ["examples.models"]}
        )
        await context.generate_schemas()
        rows = await Member.all()

``context.db()`` returns a client. The connection handler resolves clients
from the active context, and querysets/creation queries support explicit
connection selection. Pools are opened when actual database work requires them.

``init_connections=False`` is a tooling mode that does not build normal
runtime querysets. SQL previews use normal client initialization without
executing queries; see :doc:`examples/basic`.

``rakko.context.tortoise_test_context`` provides isolated test contexts and
schema setup. Current tests use it with ``tests.testmodels`` and SQLite memory
DBs. Test helper names may retain their original spelling.
