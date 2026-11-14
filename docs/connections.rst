.. Modified for Rakko ORM: document the Rakko model/query API, project identity and development workflow.

Connections and contexts
========================

``rakko.context.RakkoContext`` owns configuration, model registration and
connection cleanup for an isolated execution context.

.. code-block:: python

    async with RakkoContext() as context:
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
