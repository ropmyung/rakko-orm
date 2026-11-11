<!-- Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
Derived from Tortoise ORM; maintained and modified for Rakko ORM.
SPDX-License-Identifier: Apache-2.0 -->

# Releasing Rakko ORM

Release name: **1.0.0-alpha.1**. Package version: **1.0.0a1**. Maintainer: **ropmyung**.
Python packaging normalizes `1.0.0-alpha.1` to `1.0.0a1` (alpha number 1).
See the [version specification](https://packaging.python.org/en/latest/specifications/version-specifiers/).

## Prepare and verify

Use Python 3.12+ and uv. The commands below work in PowerShell as well as a POSIX shell.

```console
uv sync --all-groups --extra asyncpg --extra psycopg
uv run --no-sync pytest -q
uv run --no-sync pyright rakko examples docs/sphinx_autodoc_typehints.py
uv run --no-sync sphinx-build -W --keep-going -b html docs docs/_build/html
uv build --out-dir dist/releases/1.0.0a1
uv run --no-sync twine check --strict dist/releases/1.0.0a1/*.whl dist/releases/1.0.0a1/*.tar.gz
```

The version in `rakko/__init__.py`, changelog, distribution README and release
directory must agree. Refresh `uv.lock` after changing project metadata. Build into the version-specific directory so old
distributions in `dist/` cannot be uploaded accidentally. Inspect the archives
for `LICENSE.txt`, `NOTICE.txt`, `CONTRIBUTORS.rst` and `rakko/py.typed`. Install
the wheel in a fresh environment outside the source import path and run SQLite
CRUD. Verify the same version and license files when rebuilding from the sdist.
Read `LICENSE_REVIEW.md` before distributing changes derived from upstream.

`README.md` is the repository guide with local logo/documentation links.
`README.pypi.md` is the self-contained package description used for PyPI.
The repository and issue links point to https://github.com/ropmyung/rakko-orm.
A documentation site URL will be added once hosting is configured.

## Configure the public home

The public repository is https://github.com/ropmyung/rakko-orm. Keep the upstream
credits while using Rakko's own repository and issue tracker.
The package name has not been reserved by these local preparations; availability
must be checked when creating the PyPI project.

Configure a [PyPI Trusted Publisher](https://docs.pypi.org/trusted-publishers/)
for the actual repository, workflow `pypi.yml`, and environment `pypi`.
Configure TestPyPI separately with environment `testpypi` if using it. The workflow
uses OIDC, with no copied upstream secrets. It defaults to building artifacts
only; explicitly select `testpypi` or `pypi` to upload. Publish from the reviewed
release commit, using tag `v1.0.0-alpha.1` for this release.

For documentation, enable GitHub Pages with source **GitHub Actions** and run
`gh-pages.yml`. It publishes to this repository's Pages site and contains no
upstream deployment destination. The resulting site URL can then be added to
package metadata and the README.

## Release limits

This is an alpha release. SQLite execution and generated MySQL/PostgreSQL SQL
are covered by the current suite. Migration tests also run against MySQL 8.4 and PostgreSQL 16.
SQL Server/Oracle migration editors and further framework integrations need
additional validation; the docs record the tested scope.

Local release preparation does not publish to PyPI, create a GitHub release,
reserve a package name or establish a public documentation site.
