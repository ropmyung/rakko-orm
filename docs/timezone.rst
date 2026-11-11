.. Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
   Derived from Tortoise ORM; maintained and modified for Rakko ORM.
   SPDX-License-Identifier: Apache-2.0

Time zones
==========

Contexts accept ``use_tz`` and ``timezone`` options during initialization:

.. code-block:: python

    await context.init(
        db_url="sqlite://:memory:",
        modules={"models": ["examples.models"]},
        use_tz=True, timezone="UTC",
    )

The retained ``rakko.timezone`` helpers provide ``now``, timezone access and
aware/naive conversions. Coordinate datetime values, context settings and the
DB session timezone; backend conversion remains separate from field typing.
