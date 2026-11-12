<!-- Added for Rakko ORM: document the Rakko model/query API, project identity and development workflow. -->

# PyPika root exports

`pypika_tortoise-stubs` is a partial type-stub package for
[pypika-tortoise](https://github.com/tortoise/pypika-tortoise), licensed under
Apache-2.0. The PyPI 0.6.5 package imports its root API without declaring those
imports as public re-exports, which causes Pyright `reportPrivateImportUsage`.

Only the root exports are declared here. The `py.typed` marker contains
`partial`, so Pyright resolves all other modules and their types from the
installed dependency. No runtime implementation or method signature is copied.
The stubs are used through `tool.pyright.stubPath` and included in the source
distribution; they do not alter the runtime package or disable diagnostics.

Remove this workaround once the minimum supported upstream release declares
these exports. Validate changes against an unmodified PyPI install: editing
`site-packages` can hide this failure locally, including through cached links.
