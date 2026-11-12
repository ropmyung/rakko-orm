.. Modified for Rakko ORM: document the Rakko model/query API, project identity and development workflow.

Managers
========

``rakko.manager.Manager`` supplies a model's base queryset. A custom manager
can override ``get_queryset`` to define a consistent starting query.
Register it through model metadata. Model/queryset methods preserve their
constructor signature while using the manager-provided query.

Prefer the typed model entry points in :doc:`query`. Dynamic manager-specific
methods do not automatically acquire model-specific parameter signatures;
provide explicit annotations for custom APIs.
