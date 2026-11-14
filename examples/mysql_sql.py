"""Preview MySQL SQL without connecting: uv run --extra aiomysql -m examples.mysql_sql"""

from rakko import Field, Model, fields, run_async
from rakko.context import RakkoContext


class Usage(Model):
    id: Field[int] = fields.BigAutoField(unsigned=True)
    label: Field[str] = fields.CharField(100, unique=True)
    hits: Field[int] = fields.IntField(unsigned=True, default=0)
    note: Field[str | None] = fields.TextField(null=True)


async def run() -> None:
    async with RakkoContext() as context:
        await context.init(
            db_url="mysql://example:example@127.0.0.1:3306/rakko_examples",
            modules={"models": [__name__]},
        )
        # Clients connect lazily; the methods below only render SQL.
        client = context.db()
        print("Schema SQL:")
        print(client.schema_generator(client).get_create_schema_sql())

        print("Select SQL:", Usage.filter(Usage.hits >= 10).order_by(-Usage.hits).sql())
        print("Update SQL:", Usage.filter(Usage.label == "homepage").update(hits=20).sql())


if __name__ == "__main__":
    run_async(run())
