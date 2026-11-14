"""Positive typing contracts, checked by test_typing.py with Pyright."""

from typing import Any, assert_type

from rakko import Field, fields
from rakko.expressions import Criterion, Query
from rakko.indexes import Index
from rakko.migrations.constraints import CheckConstraint, UniqueConstraint
from tests.testmodels import Guild, Member, PositionalRecord


class ExtendedMember(Member):
    nickname: Field[str] = fields.CharField(100)


assert_type(Member.name, Query[Member, str])
assert_type(Member().name, str)
assert_type(Member().note, str | None)
assert_type(Member().data, dict[str, Any] | None)
assert_type(Member.age >= 18, Criterion[Member])


async def query_types(guild: Guild) -> None:
    assert_type(await Member.create(name="Alice", guild=guild), Member)
    assert_type(await Member.all().using_db(None).create(name="Bob", guild=guild), Member)
    assert_type(
        await Member.filter(Member.age >= 18).order_by(Member.age).limit(1).update(age=30), int
    )
    assert_type(await ExtendedMember.create(nickname="Al"), ExtendedMember)
    assert_type(await ExtendedMember.all().update(nickname="Al"), int)
    assert_type(
        await Member.get_or_create(Member.name == "Alice", name="Alice", guild=guild),
        tuple[Member, bool],
    )
    assert_type(await Member.update_or_create(Member.name == "Alice", age=30), tuple[Member, bool])
    assert_type(
        await ExtendedMember.get_or_create(ExtendedMember.nickname == "Al", nickname="Al"),
        tuple[ExtendedMember, bool],
    )
    assert_type(
        await ExtendedMember.update_or_create(ExtendedMember.nickname == "Al", nickname="Al"),
        tuple[ExtendedMember, bool],
    )
    assert_type(
        await PositionalRecord.get_or_create(PositionalRecord.name == "Record", None, "Record"),
        tuple[PositionalRecord, bool],
    )
    assert_type(
        await PositionalRecord.update_or_create(
            PositionalRecord.name == "Record", None, "Record", age=42
        ),
        tuple[PositionalRecord, bool],
    )
    await Member.all().only(Member.id, Member.name).first()
    await Member.all().values_list(Member.id)
    await Member.all().select_related(Member.guild).values(Member.name, Guild.name)


check_constraint = CheckConstraint[Member](check=lambda model: model.age >= 0, name="positive_age")
unique_constraint = UniqueConstraint(fields=(Member.name,), condition=lambda model: model.age >= 18)
model_index = Index(fields=(Member.age,))
