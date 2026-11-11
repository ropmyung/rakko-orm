# Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
# Derived from Tortoise ORM; maintained and modified for Rakko ORM.
# SPDX-License-Identifier: Apache-2.0

"""Run with: uv run -m examples.relations"""

from examples.models import Guild, Member
from rakko import run_async
from rakko.context import TortoiseContext
from rakko.query_utils import Prefetch


async def run() -> None:
    async with TortoiseContext() as context:
        await context.init(db_url="sqlite://:memory:", modules={"models": ["examples.models"]})
        await context.generate_schemas()

        guild = await Guild.create(name="Explorers")
        await Member.create(name="Alice", age=24, guild=guild)
        await Member.create(name="Bob", age=17, guild=guild)

        # Filter by a model instance and load the related object with a JOIN.
        members = await Member.filter(Member.guild == guild).select_related(Member.guild)
        print("Joined:", [(member.name, member.guild.name) for member in members])
        print(
            "Related columns:",
            await Member.all()
            .order_by(Member.name)
            .values(member_name=Member.name, guild_name=Guild.name),
        )

        # The reverse accessor is a descriptor, so it stays out of __init__.
        loaded = await Guild.all().prefetch_related(Guild.members).get(Guild.id == guild.id)
        print("Prefetched:", sorted(member.name for member in loaded.members))

        adults_only = Prefetch(Guild.members, Member.filter(Member.age >= 18))
        loaded = await Guild.all().prefetch_related(adults_only).get(Guild.id == guild.id)
        print("Filtered prefetch:", [member.name for member in loaded.members])

        fresh = await Member.get(Member.name == "Alice")
        await fresh.fetch_related(Member.guild)
        print("Fetched on instance:", fresh.guild.name)


if __name__ == "__main__":
    run_async(run())
