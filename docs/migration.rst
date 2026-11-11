.. Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
   Derived from Tortoise ORM; maintained and modified for Rakko ORM.
   SPDX-License-Identifier: Apache-2.0

Migration tooling status
========================

The migration framework is retained under ``rakko.migrations``. It contains
state, graph, autodetection, writer, executor and backend schema-editor layers.
The CLI exposes planning, generation, migration and SQL-preview commands.

This layer is still being adapted to Rakko's model/query declarations. The
current query and typing tests do not establish full migration compatibility
for existing upstream projects. Review generated files and SQL against the
current API and a disposable database before adopting a migration history.

For fresh disposable examples use :doc:`schema`. For API differences read
:doc:`migration_guide`; for CLI discovery use :doc:`cli`.
