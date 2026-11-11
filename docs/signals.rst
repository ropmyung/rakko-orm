.. Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
   Derived from Tortoise ORM; maintained and modified for Rakko ORM.
   SPDX-License-Identifier: Apache-2.0

Model signals
=============

Model lifecycle hooks remain in ``rakko.signals``. The retained decorators
include ``pre_save``, ``post_save``, ``pre_delete`` and ``post_delete``.
Register async receivers against the model classes concerned.

Save paths, including creation queries and instance updates, reuse the model
lifecycle implementation. Field-reference update lists are normalized to model
names before being forwarded to signal receivers and backend executors.
Bulk operations follow their own execution paths; do not assume per-instance
save hooks run for every row in a bulk query.
