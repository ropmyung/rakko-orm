.. Modified for Rakko ORM: document the Rakko model/query API, project identity and development workflow.

Design notes
============

Declarations
------------

``Field[T]`` describes values. Metaclass lookup exposes ``Query[M, T]`` on a
class; raw fields retain conversion/validation metadata and do not inherit the
SQL query wrapper.

Expressions
-----------

``Query`` and ``Criterion`` adapt native ``pypika_tortoise`` trees with model
and value types. Resolution binds fields to existing metadata, column names
and joins. The public API does not pass through ``Q`` or a replacement SQL
string builder.

Queries and backends
--------------------

``QuerySet[**P, M]`` preserves constructor parameters through cloned/chained
queries. Creation captures constructor parameters; updates/upserts preserve
supplied values without reapplying omitted defaults.

Async clients, pools, transaction contexts and schema foundations are retained
from Tortoise ORM. Rakko's independent changes focus on declarations, query
composition and type contracts. See :doc:`about` and :doc:`roadmap`.
