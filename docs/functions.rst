.. Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
   Derived from Tortoise ORM; maintained and modified for Rakko ORM.
   SPDX-License-Identifier: Apache-2.0

Functions and aggregates
========================

Function adapters accept class-level field expressions and use the existing
resolution context instead of requiring repeated field strings:

.. code-block:: python

    from rakko.functions import Count, Sum, Upper

    rows = await Member.all().values(upper_name=Upper(Member.name))
    totals = await Member.all().group_by(Guild.name).values(
        guild_name=Guild.name, count=Count(Member.id), ages=Sum(Member.age)
    )

Common adapters in ``rakko.functions`` include ``Trim``, ``Length``, ``Coalesce``,
``Lower``, ``Upper``, ``Concat``, ``Count``, ``Sum``, ``Min``, ``Max`` and ``Avg``.
Aggregates support ``distinct`` and a model-bound ``_filter`` criterion.
Backend-specific functions are retained in their ``rakko.contrib`` modules.
