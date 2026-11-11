# Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
# Derived from Tortoise ORM; maintained and modified for Rakko ORM.
# SPDX-License-Identifier: Apache-2.0

"""Run with: uv run -m examples.bulk_and_transactions"""

from examples.models import Guild, Member
from rakko import run_async
from rakko.context import TortoiseContext
from rakko.transactions import in_transaction


async def run() -> None:
    async with TortoiseContext() as context:
        await context.init(db_url="sqlite://:memory:", modules={"models": ["examples.models"]})
        await context.generate_schemas()

        guild, created = await Guild.get_or_create(Guild.name == "Explorers", name="Explorers")
        print("Guild created:", created)

        await Member.bulk_create(
            [
                Member(name="Alice", age=24, guild=guild),
                Member(name="Bob", age=17, guild=guild),
            ]
        )
        members = await Member.all().order_by(Member.id)
        for member in members:
            member.age += 1
        await Member.bulk_update(members, fields=[Member.age])
        print(
            "Bulk updated:", await Member.all().order_by(Member.id).values(Member.name, Member.age)
        )

        # Conflict and update targets accept fields, including source_field mappings.
        await Member.bulk_create(
            [Member(name="Alice", age=26, guild=guild)],
            update_fields=[Member.age],
            on_conflict=[Member.name],
        )
        alice, created = await Member.update_or_create(
            Member.name == "Alice",
            name="Alice",
            guild=guild,
            note="Updated",
        )
        print("Alice created:", created)
        alice.update_from_dict({Member.preferences: {"theme": "dark"}})
        await alice.save(update_fields=[Member.preferences])
        print(
            "Alice:",
            await Member.get(Member.id == alice.id).values(
                Member.name, Member.age, Member.note, Member.preferences
            ),
        )

        async with in_transaction() as connection:
            second_guild = await Guild.create(name="Builders").using_db(connection)
            await Member.create(connection, name="Charlie", age=30, guild=second_guild)
        print(
            "Committed guild:",
            (
                await Member.all().select_related(Member.guild).get(Member.name == "Charlie")
            ).guild.name,
        )


if __name__ == "__main__":
    run_async(run())
