.. Modified for Rakko ORM: document the Rakko model/query API, project identity and development workflow.

Model signals
=============

Model lifecycle hooks remain in ``rakko.signals``. The retained decorators
include ``pre_save``, ``post_save``, ``pre_delete`` and ``post_delete``.
Register async receivers against the model classes concerned.

Save paths, including creation queries and instance updates, reuse the model
lifecycle implementation. Field-reference update lists are normalized to model
names before being forwarded to signal receivers and backend executors.
Bulk operations follow their own execution paths; do not assume per-instance
save hooks run for every row in a bulk query.
