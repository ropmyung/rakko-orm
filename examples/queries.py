"""Run with: uv run -m examples.queries"""

from examples.models import Guild, Member
from rakko import run_async
from rakko.context import TortoiseContext
from rakko.functions import Count


async def run() -> None:
    async with TortoiseContext() as context:
        await context.init(db_url="sqlite://:memory:", modules={"models": ["examples.models"]})
        await context.generate_schemas()

        guild = await Guild.create(name="Explorers")
        await Member.bulk_create(
            [
                Member(name="Alice", age=24, guild=guild),
                Member(name="Bob", age=17, guild=guild),
                Member(name="Charlie", age=32, guild=guild),
            ]
        )

        adults = Member.filter((Member.age >= 18) & ~(Member.name == "Bob"))
        print("Adults:", await adults.order_by(-Member.age).values(Member.name, Member.age))
        print(
            "Next year:",
            await adults.order_by(Member.id).values(name=Member.name, next_age=Member.age + 1),
        )
        print(
            "Names:", await Member.all().order_by(Member.name).values_list(Member.name, flat=True)
        )

        # A field from the related model is resolved through the guild FK.
        print(
            "Members per guild:",
            await Member.all()
            .group_by(Guild.name)
            .values(guild_name=Guild.name, total=Count(Member.id)),
        )

        alice = await Member.all().only(Member.id, Member.name).get(Member.name == "Alice")
        alice.name = "Alicia"
        await alice.save(update_fields=[Member.name])
        await alice.refresh_from_db(fields=[Member.name])
        print("Partial model:", alice.name)

        await Member.filter(Member.name == "Alicia").update(
            note="Prefers evening events", preferences={"theme": "dark"}
        )
        print(
            "JSON and text:",
            await Member.get(Member.name == "Alicia").values(Member.note, Member.preferences),
        )
        print("No note:", await Member.filter(Member.note.isnull()).count())

        by_name = await Member.in_bulk(Member.age >= 18, field_name=Member.name)
        print("Lookup keys:", sorted(by_name))
        print("SQL:", adults.order_by(Member.age).sql())


if __name__ == "__main__":
    run_async(run())
