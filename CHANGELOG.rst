.. Modified for Rakko ORM: document the Rakko model/query API, project identity and development workflow.

.. _changelog:

Rakko ORM changelog
===================

This file summarizes Rakko-specific changes. The project began as a fork of
`Tortoise ORM <https://github.com/tortoise/tortoise-orm>`_; upstream releases
are not presented as Rakko release history.

1.0.0-alpha.2 — facade and release cleanup
-----------------------------------------

Maintained by ropmyung. The Python distribution version is ``1.0.0a2``.

* Expose the main facade as ``Rakko`` and export ``meta`` from the package root.
* Update framework integrations and internal calls to use the Rakko facade.
* Consolidate copyright and attribution in distribution notices while preserving
  concise modification notices in inherited files.
* Add explicit types to migration writer tests and preserve runtime validation
  coverage for invalid string conditions.
* Include migration writer tests in CI and release type checks.
* Refresh release metadata, documentation and versioned artifact paths.

1.0.0-alpha.1 — migration fixes
-------------------------------

Maintained by ropmyung. The Python distribution version is ``1.0.0a1``.

Migration fixes
~~~~~~~~~~~~~~~

* Generate Rakko imports and restore dictionary metadata in historical models.
* Preserve explicit automatic integer fields, UNSIGNED and source-column names.
* Accept expression CHECK conditions, conditional UNIQUE predicates and field
  references in UNIQUE/index declarations; serialize portable PyPika nodes.
* Use Rakko CLI configuration, operation and recorder names.
* Correct MySQL type changes, psycopg placeholders and the Windows CLI event loop.
* Preserve SQLite foreign-key data, constraints and indexes during table rebuilds.
* Commit transactional schema/history changes together and keep dry runs read-only.
* Add CLI regressions and live MySQL/PostgreSQL migration checks to CI and releases.

* Verify 206 tests, including live MySQL/PostgreSQL migration cycles.

1.0.0-alpha — first Rakko release
---------------------------------

The Python distribution version is ``1.0.0a0``.

Model and query API
~~~~~~~~~~~~~~~~~~~

* Require Python 3.12+ and use modern generic syntax.
* Expose class fields as ``Query[Model, Value]`` and instance fields as values.
* Replace the public ``Q``/keyword-filter pipeline with model-bound criteria
  built on native ``pypika_tortoise`` expressions.
* Preserve constructor parameters through ``ParamSpec`` in query chains,
  ``create``, ``update`` and both upsert methods.
* Accept field references in projections, sorting, grouping, relation loading,
  bulk field lists, instance updates and refreshes. Named projections accept SQL expressions.
* Add ``@meta``/``MetaOption`` metadata and ``@reverse_relation`` accessors.

Fields and execution
~~~~~~~~~~~~~~~~~~~~

* Separate automatic integer factories from ordinary fields; a primary key
  alone no longer enables auto-increment.
* Support signed/unsigned integer sizes and MySQL UNSIGNED/AUTO_INCREMENT SQL.
* Preserve nullable Text/JSON typing, async drivers, pooling and transactions.
* Keep updates partial and upsert lookup separate from creation values;
  preserve uniqueness-race retries and explicit transaction connections.
* Correct renamed-column handling in bulk conflict SQL and related partial selection.

Project and validation
~~~~~~~~~~~~~~~~~~~~~~

* Establish Rakko's sea-otter identity and ocean-blue documentation.
* Replace inherited release notes and stale examples with concise Rakko guides.
* Add runnable examples plus runtime, SQL-generation and Pyright regression tests.

Next work
~~~~~~~~~

An explicit JOIN builder, remaining framework integrations and broader backend
validation remain follow-up work.
