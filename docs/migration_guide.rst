.. Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
   Derived from Tortoise ORM; maintained and modified for Rakko ORM.
   SPDX-License-Identifier: Apache-2.0

Moving from Tortoise ORM
========================

Rakko started from Tortoise ORM's source and now has its own API. Import
``rakko`` and follow this checkout's examples.

.. list-table:: Main API changes
   :header-rows: 1
   :widths: 40 60

   * - Earlier pattern
     - Rakko pattern
   * - Unannotated model fields
     - ``name: Field[str] = fields.CharField(100)``
   * - Implicit generation on an integer primary key
     - Choose ``AutoField``/``BigAutoField`` explicitly
   * - ``filter(name="Ada")`` or ``Q(name="Ada")``
     - ``filter(User.name == "Ada")``
   * - ``get(id=1)``
     - ``get(User.id == 1)``
   * - Repeated field strings
     - ``values(User.name)``, ``order_by(-User.age)``, ``only(User.id)``
   * - ``get_or_create(..., defaults={...})``
     - ``get_or_create(User.name == "Ada", name="Ada")``
   * - Untyped nested metadata
     - ``@meta`` with ``class Meta(MetaOption)``
   * - Reverse fields resembling constructor parameters
     - ``@reverse_relation`` on a typed accessor

Lookups receive a single model-bound criterion. ``ParamSpec`` preserves model
arguments, and raw fields remain metadata rather than SQL operators.
Regular constructor parameters are optional statically; runtime validation and
DB constraints govern saves. Automatic IDs remain excluded.

``TortoiseContext``, ``TortoiseConfig`` and some configuration/integration names
are retained inside ``rakko``. They do not require installing the separate
``tortoise`` package. Review existing migrations/integrations against the changed API.
