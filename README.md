<!-- Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
Derived from Tortoise ORM; maintained and modified for Rakko ORM.
SPDX-License-Identifier: Apache-2.0 -->

<p align="center">
  <img src="docs/_static/rakko-logo.png" width="160" height="160" alt="Rakko ORM — a sea otter in an ocean wave">
</p>

# Rakko ORM

**Typed queries. Async by nature.**

**1.0.0-alpha** · Python package version **1.0.0a0** · Maintained by **ropmyung**.

Rakko ORM is an asynchronous Python ORM built around typed model fields,
natural Python conditions and MySQL-friendly database access.
Its name comes from *rakko*, the Japanese word for sea otter (해달).

```python
members = await Member.filter(
    (Member.age >= 18) & (Member.guild == guild)
).order_by(-Member.age).values(Member.name, Member.age)
```

Rakko began as a fork of [Tortoise ORM](https://github.com/tortoise/tortoise-orm).
It is now developed as a separate project with its own package, API direction,
documentation and identity. Tortoise's async database foundation is retained;
Rakko redesigns model typing, field declarations and query composition.

## What changes

- **Fields with two views:** `Member.age` is a typed query expression; `member.age` is a Python value.
- **Python conditions:** combine comparisons with `&`, `|` and `~`, then pass one model-bound `Criterion`.
- **Field references throughout:** projections, ordering, grouping, relations and bulk field lists use model attributes.
- **Constructor-aware calls:** `ParamSpec` preserves model parameter names and value types through query chains and upserts.
- **Explicit automatic integers:** `AutoField`, `BigAutoField`, `SmallAutoField` and `TinyAutoField` are separate from ordinary integers. A primary key alone does not enable auto-increment.
- **MySQL support:** async drivers, pooling, transactions and signed/unsigned integer fields.
- **Model metadata and reverse accessors:** `@meta`, `MetaOption` and `@reverse_relation` provide explicit declarations.

SQL construction uses `pypika_tortoise`; database connections and transaction
management build on the existing async backend adapters.

## Try this checkout

Python **3.12 or newer** is required. These commands install and run the local
project; they do not assume that a Rakko release is available on PyPI.

```powershell
uv sync --group test
uv run -m examples.basic
uv run -m examples.queries
uv run -m examples.relations
uv run -m examples.bulk_and_transactions
```

The examples use isolated in-memory SQLite databases. To preview MySQL SQL,
including UNSIGNED and AUTO_INCREMENT, without connecting to a server:

```powershell
uv run --extra aiomysql -m examples.mysql_sql
```

## A small application

```python
import asyncio

from rakko import Field, Model, fields
from rakko.context import TortoiseContext


class User(Model):
    id: Field[int] = fields.AutoField()
    name: Field[str] = fields.CharField(100)
    age: Field[int | None] = fields.IntField(null=True)


async def main() -> None:
    async with TortoiseContext() as context:
        await context.init(db_url="sqlite://:memory:", modules={"models": [__name__]})
        await context.generate_schemas()

        user = await User.create(name="Ada")
        await User.filter(User.id == user.id).update(age=21)
        print(await User.all().values(User.name, User.age))


if __name__ == "__main__":
    asyncio.run(main())
```

Ordinary model parameters are optional in static constructor signatures while
field names and value types remain checked. Runtime validation and database
constraints still determine whether a record can be saved. Updates change only
the explicitly supplied fields. `create`, `get_or_create` and `update_or_create`
accept model arguments directly; upsert criteria are used only for lookup.

## Read and contribute

- [Getting started](docs/getting_started.rst)
- [Model and field declarations](docs/models.rst)
- [Query API](docs/query.rst)
- [Changes from Tortoise ORM](docs/migration_guide.rst)
- [Runnable examples](examples/README.md)
- [Development and contribution guide](docs/CONTRIBUTING.rst)
- [Concise changelog](CHANGELOG.rst)
- [Release preparation and publishing](RELEASING.md)
- [License review](LICENSE_REVIEW.md)

```powershell
uv run --all-groups --extra asyncpg --extra psycopg pytest -q
uv run --group docs sphinx-build -W --keep-going -b html docs docs/_build/html
```

The test suite exercises SQLite execution, generated MySQL/PostgreSQL SQL and
Pyright typing contracts. The migration framework and additional integrations
are retained from the original codebase and are still being adapted to Rakko's API.

## Origins and license

Rakko ORM is distributed under [Apache License 2.0](LICENSE.txt).
The original [Tortoise ORM](https://github.com/tortoise/tortoise-orm) authors and
contributors are acknowledged in [NOTICE.txt](NOTICE.txt) and
[CONTRIBUTORS.rst](CONTRIBUTORS.rst). Upstream release history is separate from
[Rakko's changelog](CHANGELOG.rst).
