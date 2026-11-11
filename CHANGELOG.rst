.. Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
   Derived from Tortoise ORM; maintained and modified for Rakko ORM.
   SPDX-License-Identifier: Apache-2.0

.. _changelog:

Rakko ORM changelog
===================

1.0.0-alpha — first Rakko release
---------------------------------

Maintained by ropmyung. The Python distribution version is ``1.0.0a0``.

This file summarizes Rakko-specific changes. The project began as a fork of
`Tortoise ORM <https://github.com/tortoise/tortoise-orm>`_; upstream releases
are not presented as Rakko release history.

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

An explicit JOIN builder, broader live-database validation, and adaptation of
inherited migration/integration tooling remain follow-up work.
