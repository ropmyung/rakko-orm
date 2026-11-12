.. Modified for Rakko ORM: document the Rakko model/query API, project identity and development workflow.

Native SQL and PyPika
=====================

The normal ORM path uses model-bound criteria around PyPika expressions.
For native criteria, wrap them with the model type as shown in :doc:`expressions`.
``Model.raw(sql)`` and client query methods remain available for explicit SQL.

Raw SQL is the caller's responsibility. Prefer the normal parameterized ORM
path for application values. Do not construct SQL by interpolating user data.
``QuerySet.sql()`` renders a query for inspection; it does not execute it.
The MySQL :doc:`examples/basic` demonstrate a SQL-only preview without a server.
