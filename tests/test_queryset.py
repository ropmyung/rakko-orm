import asyncio
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio

from rakko.context import RakkoContext, tortoise_test_context
from rakko.exceptions import FieldError, ValidationError
from rakko.functions import Count
from rakko.query_utils import Prefetch
from rakko.queryset import CreateQuery
from rakko.transactions import in_transaction
from tests.testmodels import DualGuild, Guild, Member, PositionalRecord, Unrelated


@pytest_asyncio.fixture
async def query_db() -> AsyncIterator[RakkoContext]:
    async with tortoise_test_context(["tests.testmodels"]) as context:
        yield context


@pytest_asyncio.fixture
async def members(query_db: RakkoContext) -> tuple[Member, Member]:
    guild = await Guild.create(name="Guild")
    alice = await Member.create(name="Alice", age=20, guild=guild)
    bob = await Member.create(name="Bob", age=30, guild=guild)
    return alice, bob


@pytest.mark.asyncio
async def test_create_is_lazy_and_nullable_fields_can_be_omitted(query_db: RakkoContext) -> None:
    guild = await Guild.create(name="Guild")
    query = Member.create(name="Alice", guild=guild)
    assert isinstance(query, CreateQuery)
    assert await Member.all().count() == 0
    member = await query
    assert member.id > 0
    assert member.age == 0
    assert member.note is None
    assert member.data is None


@pytest.mark.asyncio
async def test_projection_accepts_fields_and_keeps_string_compatibility(
    members: tuple[Member, Member],
) -> None:
    query = Member.all().order_by(Member.age)
    assert await query.values(Member.name, Member.age) == [
        {"name": "Alice", "age": 20},
        {"name": "Bob", "age": 30},
    ]
    assert await query.values(label=Member.name) == [{"label": "Alice"}, {"label": "Bob"}]
    assert await query.values_list(Member.name, Member.age) == [("Alice", 20), ("Bob", 30)]
    assert await query.values_list(Member.name, flat=True) == ["Alice", "Bob"]
    assert await query.values("name", "age") == await query.values(Member.name, Member.age)


@pytest.mark.asyncio
async def test_field_ordering_latest_earliest_and_chaining(members: tuple[Member, Member]) -> None:
    alice, bob = members
    assert await Member.all().order_by(-Member.age).limit(1).values_list(Member.id, flat=True) == [
        bob.id
    ]
    latest = await Member.latest(Member.age)
    earliest = await Member.earliest(Member.age)
    assert latest is not None and latest.id == bob.id
    assert earliest is not None and earliest.id == alice.id
    assert await Member.filter(Member.age >= 20).exclude(Member.name == "Alice").count() == 1


@pytest.mark.asyncio
async def test_grouping_and_related_projection(members: tuple[Member, Member]) -> None:
    rows = (
        await Member.all()
        .group_by(Guild.name)
        .annotate(total=Count(Member.id))
        .values(Guild.name, "total")
    )
    assert rows == [{"guild__name": "Guild", "total": 2}]
    assert await Member.all().order_by(Member.id).values(guild_name=Guild.name) == [
        {"guild_name": "Guild"},
        {"guild_name": "Guild"},
    ]


@pytest.mark.asyncio
async def test_only_save_and_refresh_accept_fields(members: tuple[Member, Member]) -> None:
    alice, _ = members
    member = await Member.all().only(Member.id, Member.name).get(Member.id == alice.id)
    with pytest.raises(AttributeError):
        _ = member.age
    member.name = "Updated"
    await member.save(update_fields=[Member.name])
    await alice.refresh_from_db(fields=[Member.name])
    assert alice.name == "Updated"
    assert alice.age == 20


@pytest.mark.asyncio
async def test_relation_loading_and_prefetch_descriptor(members: tuple[Member, Member]) -> None:
    alice, _ = members
    member = await Member.all().select_related(Member.guild).get(Member.id == alice.id)
    assert member.guild.name == "Guild"
    guild = await Guild.all().prefetch_related(Guild.members).first()
    assert guild is not None
    assert sorted(member.name for member in guild.members) == ["Alice", "Bob"]
    guild = (
        await Guild.all()
        .prefetch_related(
            Prefetch(Guild.members, Member.filter(Member.age < 25), to_attr="young_members")
        )
        .first()
    )
    assert guild is not None
    assert [member.name for member in getattr(guild, "young_members")] == ["Alice"]
    fresh = await Member.get(Member.id == alice.id)
    await fresh.fetch_related(Member.guild)
    assert fresh.guild.name == "Guild"


@pytest.mark.asyncio
async def test_in_bulk_bulk_update_and_partial_update(members: tuple[Member, Member]) -> None:
    alice, bob = members
    by_name = await Member.in_bulk(Member.age >= 20, field_name=Member.name)
    assert set(by_name) == {"Alice", "Bob"}
    assert await Member.filter(Member.id == alice.id).update(note="Only note") == 1
    assert (await Member.get(Member.id == alice.id)).name == "Alice"
    alice.age, bob.age = 21, 31
    assert await Member.bulk_update([alice, bob], fields=[Member.age]) == 2
    assert await Member.all().order_by(Member.id).values_list(Member.age, flat=True) == [21, 31]


@pytest.mark.asyncio
async def test_bulk_conflict_fields_use_database_column_names(query_db: RakkoContext) -> None:
    await Guild.create(name="Guild")
    await Guild.bulk_create(
        [Guild(name="Guild")], update_fields=[Guild.name], on_conflict=[Guild.name]
    )
    assert await Guild.all().count() == 1


@pytest.mark.asyncio
async def test_union_ordering_accepts_fields(members: tuple[Member, Member]) -> None:
    alice, bob = members
    query = (
        Member.filter(Member.id == alice.id)
        .union(Member.filter(Member.id == bob.id))
        .order_by(-Member.age)
    )
    assert [member.id for member in await query] == [bob.id, alice.id]
    assert [member.name for member in await query.order_by(-Member.name)] == ["Bob", "Alice"]


@pytest.mark.asyncio
async def test_invalid_and_ambiguous_field_references_fail(query_db: RakkoContext) -> None:
    with pytest.raises(FieldError, match="unambiguously"):
        Member.all().values(Unrelated.name)
    with pytest.raises(FieldError, match="unambiguously"):
        DualGuild.all().values(Guild.name)
    with pytest.raises(FieldError, match="belonging"):
        Member.all().bulk_update([], fields=[Guild.name])
    with pytest.raises(FieldError, match="Duplicate"):
        Member.all().values(Member.name, "name")
    with pytest.raises(FieldError, match="field reference"):
        Member.all().only(Member.age + 1)


@pytest.mark.asyncio
async def test_nullable_json_text_and_single_result_projection(
    members: tuple[Member, Member],
) -> None:
    alice, _ = members
    payload = {"nested": [1, None, "value"]}
    assert await Member.filter(Member.id == alice.id).update(data=payload, note="Note") == 1
    row = await Member.get(Member.id == alice.id).values(payload=Member.data, note=Member.note)
    assert row == {"payload": payload, "note": "Note"}
    assert await Member.filter(Member.note.isnull()).count() == 1
    assert await Member.filter(Member.age.isin([])).count() == 0
    assert await Member.filter(Member.age.notin([])).count() == 2


@pytest.mark.asyncio
async def test_select_only_related_fields(members: tuple[Member, Member]) -> None:
    member = await Member.all().only(Member.id, Guild.name).first()
    assert member is not None
    assert member.guild.name == "Guild"
    with pytest.raises(AttributeError):
        _ = member.name


@pytest.mark.asyncio
async def test_create_query_uses_transaction_connection(query_db: RakkoContext) -> None:
    with pytest.raises(RuntimeError, match="rollback"):
        async with in_transaction() as connection:
            await Guild.create(name="Temporary").using_db(connection)
            await Guild.create(connection, name="Also temporary")
            raise RuntimeError("rollback")
    assert await Guild.all().count() == 0


@pytest.mark.asyncio
async def test_criteria_are_parameterized(members: tuple[Member, Member]) -> None:
    malicious = "Alice' OR 1=1 --"
    query = Member.filter(Member.name == malicious)
    assert malicious not in query.sql()
    assert await query == []


@pytest.mark.asyncio
async def test_named_projection_expressions_do_not_change_parent_query(
    members: tuple[Member, Member],
) -> None:
    query = Member.all().order_by(Member.id)
    assert await query.values(next_age=Member.age + 1) == [{"next_age": 21}, {"next_age": 31}]
    assert await query.values(Member.age) == [{"age": 20}, {"age": 30}]
    assert await Member.all().values(total=Count(Member.id)) == [{"total": 2}]
    grouped = Member.all().annotate(total=Count(Member.id))
    assert await grouped.values_list("total", flat=True) == [2]
    assert await grouped.values(renamed="total") == [{"renamed": 2}]
    rows = await grouped.values()
    assert "0" not in rows[0] and "renamed" not in rows[0]


@pytest.mark.asyncio
async def test_upsert_parameters_and_instance_field_mappings(query_db: RakkoContext) -> None:
    guild, created = await Guild.get_or_create(Guild.name == "Guild", name="Guild")
    assert created
    same, created = await Guild.get_or_create(Guild.name == "Guild", name="Unused")
    assert not created and same.id == guild.id
    updated, created = await Guild.update_or_create(Guild.id == guild.id, name="Updated")
    assert not created and updated.name == "Updated"
    updated.update_from_dict({Guild.name: "Final"})
    await updated.save(update_fields=[Guild.name])
    assert (await Guild.get(Guild.id == guild.id)).name == "Final"
    another, created = await Guild.update_or_create(Guild.name == "Another", name="Another")
    assert created and another.name == "Another"


@pytest.mark.asyncio
async def test_upsert_preserves_omitted_values(members: tuple[Member, Member]) -> None:
    alice, _ = members
    updated, created = await Member.update_or_create(Member.id == alice.id, note="Updated")
    assert not created
    assert updated.name == "Alice" and updated.age == 20
    assert updated.note == "Updated"
    unchanged, created = await Member.get_or_create(Member.id == alice.id, age=99)
    assert not created and unchanged.age == 20


@pytest.mark.asyncio
async def test_upsert_accepts_positional_constructor_arguments(query_db: RakkoContext) -> None:
    record, created = await PositionalRecord.get_or_create(
        PositionalRecord.name == "Record", None, "Record", age=42
    )
    assert created and record.age == 42
    updated, created = await PositionalRecord.update_or_create(
        PositionalRecord.id == record.id, None, "Renamed"
    )
    assert not created and updated.name == "Renamed" and updated.age == 42
    another, created = await PositionalRecord.update_or_create(
        PositionalRecord.name == "Another", None, "Another", age=24
    )
    assert created and another.age == 24


@pytest.mark.asyncio
async def test_upsert_uses_supplied_transaction(query_db: RakkoContext) -> None:
    with pytest.raises(RuntimeError, match="rollback"):
        async with in_transaction() as connection:
            await Guild.get_or_create(Guild.name == "New", connection, name="New")
            await Guild.update_or_create(Guild.name == "Other", connection, name="Other")
            raise RuntimeError("rollback")
    assert await Guild.all().count() == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("method_name", ["get_or_create", "update_or_create"])
async def test_concurrent_upsert_reuses_unique_record(
    query_db: RakkoContext, method_name: str
) -> None:
    operation = getattr(Guild, method_name)
    results = await asyncio.gather(
        *(operation(Guild.name == "Concurrent", name="Concurrent") for _ in range(3))
    )
    assert sum(created for _, created in results) == 1
    assert len({guild.id for guild, _ in results}) == 1
    assert await Guild.all().count() == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("method_name", ["get_or_create", "update_or_create"])
async def test_upsert_does_not_infer_creation_values_from_criterion(
    query_db: RakkoContext, method_name: str
) -> None:
    with pytest.raises(ValidationError):
        await getattr(Guild, method_name)(Guild.name == "Not inferred")
    assert await Guild.all().count() == 0


def test_raw_fields_are_not_sql_expressions() -> None:
    from pypika_tortoise.terms import Term

    from rakko import fields

    field = fields.IntField()
    assert not isinstance(field, Term)
    with pytest.raises(TypeError):
        _ = field + 1


@pytest.mark.asyncio
async def test_mysql_sql_uses_field_references(
    query_db: RakkoContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    from pypika_tortoise import MySQLQuery

    from rakko import fields
    from rakko.backends.mysql.client import MySQLClient

    client = MySQLClient(
        user="test",
        password="test",
        database="test",
        host="localhost",
        port=3306,
        connection_name="test",
    )
    monkeypatch.setattr(Member._meta, "basequery", MySQLQuery.from_(Member._meta.basetable))
    query = (
        Member.filter(Member.age >= 18).using_db(client).order_by(-Member.age).values(Member.name)
    )
    sql = query.sql()
    assert "`display_name`" in sql
    assert "`age`>=%s" in sql
    assert "`age` DESC" in sql
    auto = fields.BigAutoField(unsigned=True)
    assert (
        auto.get_for_dialect("mysql", "GENERATED_SQL")
        == "BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT"
    )
    assert not fields.IntField(primary_key=True).generated


@pytest.mark.asyncio
async def test_lock_targets_accept_models(
    query_db: RakkoContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    from pypika_tortoise import PostgreSQLQuery

    from rakko.backends.base.client import Capabilities

    table = Member._meta.basetable
    monkeypatch.setattr(Member._meta.db, "capabilities", Capabilities("postgres"))
    monkeypatch.setattr(
        Member._meta,
        "basequery_all_fields",
        PostgreSQLQuery.from_(table).select(
            *(table[column] for column in Member._meta.fields_db_projection.values())
        ),
    )
    sql = Member.all().select_related(Member.guild).select_for_update(of=(Member, Guild)).sql()
    assert "FOR UPDATE OF" in sql
    assert '"member"' in sql.split("FOR UPDATE OF", 1)[1]
    assert '"member__guild"' in sql.split("FOR UPDATE OF", 1)[1]
