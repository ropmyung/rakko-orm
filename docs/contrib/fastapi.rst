.. Modified for Rakko ORM: document the Rakko model/query API, project identity and development workflow.

FastAPI
=======

``rakko.contrib.fastapi.RegisterTortoise`` retains the lifespan context adapter
for model initialization and connection cleanup. Configure its model modules
with Rakko declarations and use model-bound criteria in handlers.

The adapter's historical name is retained. Framework-specific executable
examples are not yet included in this checkout; the current :doc:`../examples/basic`
provide the validated model/query workflow. Integration adaptation is tracked
in :doc:`../roadmap`.
