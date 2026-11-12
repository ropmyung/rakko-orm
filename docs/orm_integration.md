<!-- Modified for Rakko ORM: document the Rakko model/query API, project identity and development workflow. -->

# Rakko model and query integration

The extension experiments are integrated into `rakko`: typed `Field[T]`,
automatic integer factories, `@meta`/`MetaOption`, and `@reverse_relation`.
Class fields expose `Query` objects; raw fields remain declaration metadata.

Queries use model-bound criteria and native `pypika_tortoise` trees.
`QuerySet`, creation, updates and upserts preserve constructor parameters with
`ParamSpec`. Upserts take direct model arguments rather than a `defaults` mapping.

See [design](design.rst), [models](models.rst), [queries](query.rst),
[changes](../CHANGELOG.rst) and [origins](about.rst).
