# Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
# Derived from Tortoise ORM; maintained and modified for Rakko ORM.
# SPDX-License-Identifier: Apache-2.0

"""Run with: uv run -m examples.basic"""

from datetime import datetime as dt

from rakko import Field, MetaOption, Model, fields, run_async
from rakko.context import TortoiseContext
from rakko.models import meta


class Event(Model):
    id: Field[int] = fields.AutoField(primary_key=True)
    name: Field[str] = fields.TextField()
    datetime: Field[dt | None] = fields.DatetimeField(null=True)
    username: Field[str] = fields.CharField(max_length=150, unique=True, db_index=True)

    @meta
    class Meta(MetaOption):
        table = "event"

    def __str__(self) -> str:
        return self.name


async def run() -> None:
    async with TortoiseContext() as context:
        await context.init(db_url="sqlite://:memory:", modules={"models": [__name__]})
        await context.generate_schemas()

        # Generated IDs and nullable fields can be omitted.
        event = await Event.create(name="Test", username="test")
        assert event.datetime is None

        # A partial update changes only the supplied fields.
        await Event.filter(Event.id == event.id).update(name="Updated name")
        found = await Event.get(Event.id == event.id)
        print("Updated:", found.name)

        await Event(name="Test 2", username="test2").save()
        print("IDs:", await Event.all().order_by(Event.id).values_list(Event.id, flat=True))
        print("Rows:", await Event.all().order_by(Event.id).values(Event.id, Event.name))

        await Event.all().delete(Event.username == "test2")
        print("Remaining:", await Event.all().count())


if __name__ == "__main__":
    run_async(run())
