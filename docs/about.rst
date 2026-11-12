.. Modified for Rakko ORM: document the Rakko model/query API, project identity and development workflow.

Origins, identity and status
============================

Rakko means sea otter
---------------------

Rakko ORM takes its name from the Japanese word for sea otter (해달).
The new sea-otter-and-wave emblem and ocean-blue palette express its own identity.
The logo and generation prompt are stored locally under ``docs/_static``.

Project origins
---------------

Rakko began by copying/forking the source of
`Tortoise ORM <https://github.com/tortoise/tortoise-orm>`_. The original async
backend foundation is retained. Rakko now develops a separate model/query API,
package, documentation and design direction. Upstream release history is separate.

The :doc:`license` page preserves the Apache License 2.0 text. ``NOTICE.txt`` identifies
the original project and Rakko modifications. :doc:`CONTRIBUTORS` preserves
upstream acknowledgements; original authors are not presented as maintainers
of this independent project.

Current status
--------------

Tests exercise SQLite CRUD, relations, projections, transactions, partial
updates, concurrent upserts, runnable examples and Pyright contracts. MySQL
and PostgreSQL SQL generation are also covered. This is a development project;
further integration work and an explicit JOIN builder are planned. Migration CLI
tests also exercise live MySQL/PostgreSQL apply and rollback cycles.
See :doc:`CHANGELOG` and :doc:`roadmap`.

.. toctree::
   :hidden:

   license
