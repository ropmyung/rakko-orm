.. Modified for Rakko ORM: document the Rakko model/query API, project identity and development workflow.

Expressions
===========

Rakko adapts native ``pypika_tortoise`` trees to model metadata and backend
columns. ``Query[M, T]`` carries model/value types; ``Criterion[M]`` carries
the model a condition is intended to filter.

.. code-block:: python

    condition = (Member.age >= 18) & (Member.guild == guild)
    members = await Member.filter(condition)
    rows = await Member.all().values(next_age=Member.age + 1)

Class fields support comparison and arithmetic. A raw ``fields.IntField()``
is declaration metadata and does not build SQL. Use ``&``, ``|`` and ``~``
rather than Python's ``and``, ``or`` and ``not``.

Native criteria and annotations
-------------------------------

Wrap a native condition in the intended model type:

.. code-block:: python

    from rakko import Criterion

    table = Member.get_table()
    members = await Member.filter(Criterion[Member](table.age >= 18))

For a named annotation, a typed ``Query`` can wrap ``F``:

.. code-block:: python

    from rakko import Query
    from rakko.expressions import F
    from rakko.functions import Count

    total: Query[Member, int] = Query(F("total"))
    rows = await Member.annotate(total=Count(Member.id)).filter(total >= 1).values("total")

Named projections and aggregates accept fields directly. ``F``, ``RawSQL``
and ``Subquery`` remain explicit integration helpers. Caller-supplied raw SQL
is passed through as SQL text.

Typing boundaries
-----------------

The current update signature copies constructor value types. It does not
automatically widen values to SQL expressions or encode database requiredness.
Typed SQL-expression assignments in updates are further design work; see
:doc:`roadmap`. Field-reference lists are already supported in :doc:`query`.
