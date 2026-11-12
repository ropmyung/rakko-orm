.. Modified for Rakko ORM: document the Rakko model/query API, project identity and development workflow.

Application integrations
========================

Adapters are retained under ``rakko.contrib``. Historical helper names such
as ``register_tortoise`` and ``RegisterTortoise`` remain in their APIs. The
query/declaration redesign is tested directly; broader application integration
coverage is still being expanded.

.. toctree::
   :maxdepth: 1

   contrib/fastapi
   contrib/starlette
   contrib/aiohttp
   contrib/blacksheep
   contrib/quart
   contrib/sanic
   contrib/pydantic
   contrib/unittest
   contrib/linters
   contrib/mysql
   contrib/postgres
