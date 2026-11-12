.. Modified for Rakko ORM: document the Rakko model/query API, project identity and development workflow.

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
