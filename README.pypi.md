<!-- Modified for Rakko ORM: document the Rakko model/query API, project identity and development workflow. -->

# Rakko ORM

**Typed queries. Async by nature.**

Rakko ORM is an independent asynchronous Python ORM maintained by **ropmyung**.
Release **1.0.0-alpha.3** uses the Python package version **1.0.0a3** and requires
Python **3.12 or newer**. Its name means sea otter (해달).

Rakko began as a fork of [Tortoise ORM](https://github.com/tortoise/tortoise-orm).
It retains the async database foundation while redesigning field typing,
model metadata and query composition. It is developed as a separate project.

```python
import asyncio

from rakko import Field, Model, fields
from rakko.context import RakkoContext


class User(Model):
    id: Field[int] = fields.AutoField()
    name: Field[str] = fields.CharField(100)
    age: Field[int | None] = fields.IntField(null=True)


async def main() -> None:
    async with RakkoContext() as context:
        await context.init(db_url="sqlite://:memory:", modules={"models": [__name__]})
        await context.generate_schemas()
        user = await User.create(name="Ada", age=20)
        await User.filter(User.id == user.id).update(age=21)
        print(await User.filter(User.age >= 18).values(User.name, User.age))


if __name__ == "__main__":
    asyncio.run(main())
```

- Class fields are model-bound query expressions; instance fields are Python values.
- Conditions use Python comparisons and `&`, `|`, `~`; filtering takes one criterion.
- Projections, sorting, grouping and relation loading accept field references.
- `ParamSpec` preserves model constructor names and types through query chains and upserts.
- Automatic integer fields are explicit; setting a primary key alone does not enable auto-increment.
- MySQL signed/unsigned integers, async drivers, connection pools and transactions are retained.

Ordinary constructor parameters are optional in static signatures; runtime
validation and database constraints still apply. Updates modify supplied fields.
SQL expressions use `pypika_tortoise`. An explicit JOIN builder and further framework integration work remain planned.
Migration tests cover SQLite, MySQL and PostgreSQL application and reversal.

SQLite works with the base package. MySQL drivers are available through the
`aiomysql` and `asyncmy` extras. PostgreSQL drivers use `asyncpg` or `psycopg`.
The source distribution includes documentation sources, examples and tests.

Rakko ORM is distributed under the
[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0).
`LICENSE.txt`, `NOTICE.txt` and `CONTRIBUTORS.rst` accompany distributions and
preserve upstream licensing and credits. No upstream endorsement is implied.
