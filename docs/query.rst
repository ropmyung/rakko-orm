.. Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
   Derived from Tortoise ORM; maintained and modified for Rakko ORM.
   SPDX-License-Identifier: Apache-2.0

Querying
========

Conditions
----------

``filter``, ``exclude``, ``get`` and ``get_or_none`` receive one
``Criterion[Model]``. Combine comparisons with ``&``, ``|`` and ``~``:

.. code-block:: python

    adults = Member.filter((Member.age >= 18) & ~(Member.name == "Bob"))
    rows = await adults.order_by(-Member.age).values(Member.name, Member.age)

Queryset ``count``, ``exists``, ``update`` and ``delete`` can additionally
receive one optional criterion. Use ``isnull``, ``notnull``, ``isin`` and
``notin`` on fields. The public condition API no longer takes ``Q`` trees or
old keyword filters.

Field references
----------------

Fields are accepted by ``values``, ``values_list``, ``only``, ``order_by``,
``latest``, ``earliest``, ``group_by``, ``select_related``, ``prefetch_related``,
``Prefetch``, ``in_bulk`` and bulk field lists. Instance save/refresh/fetch
operations accept them too. Named projections can contain expressions:

.. code-block:: python

    names = await Member.all().values_list(Member.name, flat=True)
    rows = await Member.all().values(name=Member.name, next_age=Member.age + 1)
    totals = await Member.all().group_by(Guild.name).values(
        guild_name=Guild.name, total=Count(Member.id)
    )

A related field resolves through an unambiguous direct relation. For multiple
possible paths, supply an explicit string path. Annotation names, output
labels and index names can still be strings.

Create, update and delete
-------------------------

.. code-block:: python

    member = await Member.create(name="Ada", guild=guild)
    await Member.filter(Member.id == member.id).update(age=21)
    await Member.all().delete(Member.name == "Temporary")

Creation returns an awaitable ``CreateQuery``. Select a connection with
``.using_db(connection)`` or the first positional argument. The optional
criterion to queryset ``update`` is positional-only. ``ParamSpec`` preserves
constructor parameter names/types; updates modify only supplied fields.

Upserts
-------

Pass a criterion followed by typed model arguments. An optional connection is
the second positional argument:

.. code-block:: python

    guild, created = await Guild.get_or_create(
        Guild.name == "Explorers", name="Explorers"
    )
    member, created = await Member.update_or_create(Member.id == member.id, age=30)

``get_or_create`` leaves an existing record unchanged. ``update_or_create``
changes only supplied values, without reapplying omitted defaults. Lookup
criteria are never converted into creation values. Supply required save data
if creation may be needed. Uniqueness-race retries use the same lookup.

Bulk operations
---------------

.. code-block:: python

    await Member.bulk_update(members, fields=[Member.age])
    await Member.bulk_create(
        [Member(name="Ada", age=22, guild=guild)],
        update_fields=[Member.age], on_conflict=[Member.name],
    )

See :doc:`examples/basic` for executable nullable-field, relation, partial-model
and transaction workflows.
