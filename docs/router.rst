.. Modified for Rakko ORM: document the Rakko model/query API, project identity and development workflow.

Database routing
================

Router configuration is retained through the context's ``routers`` option.
Routers may select clients for reads and writes. Queryset ``using_db`` and
explicit creation/upsert connections select a specific connection instead.

Keep routing configuration consistent with registered connection names and
model apps. See :doc:`connections` for context ownership and :doc:`transactions`
for explicit transaction selection.
