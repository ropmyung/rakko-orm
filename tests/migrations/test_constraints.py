from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Self
from unittest.mock import Mock

import pytest
import pytest_asyncio
from pypika_tortoise.context import DEFAULT_SQL_CONTEXT
from pypika_tortoise.terms import Criterion as SQLCriterion

from rakko import Field, MetaOption, Model, fields
from rakko.context import RakkoContext
from rakko.exceptions import IntegrityError
from rakko.expressions import Criterion
from rakko.migrations.constraints import CheckConstraint, UniqueConstraint
from rakko.migrations.operations import AddConstraint, RemoveConstraint, RenameConstraint
from rakko.migrations.schema_generator.state import ModelState
from rakko.migrations.schema_generator.state_diff import StateModelDiff
from rakko.migrations.writer import ImportManager, render_value


class Account(Model):
    id: Field[int] = fields.AutoField()
    balance: Field[int] = fields.IntField(source_field="stored_balance")

    Meta = MetaOption(table="accounts")

    @Meta.check_constraint
    @staticmethod
    def positive_balance(model: type[Account]) -> Criterion[Account]:
        return model.balance >= 0

    @Meta.unique_constraint(balance)
    @classmethod
    def unique_positive_balance(cls) -> Criterion[Self]:
        return cls.balance > 0


@pytest_asyncio.fixture
async def account_context() -> AsyncIterator[RakkoContext]:
    async with RakkoContext() as context:
        await context.init(db_url="sqlite://:memory:", modules={"models": [__name__]})
        yield context


@pytest.mark.asyncio
async def test_decorator_registers_and_defers_check(account_context: RakkoContext) -> None:
    constraint = Account.Meta["constraints"][0]
    assert constraint is Account.positive_balance
    assert constraint.name == "positive_balance"
    assert callable(constraint.check)
    callback = Mock(return_value=Account.balance >= 0)
    check = CheckConstraint[Account](callback, "positive")
    assert check.get_sql(Account, DEFAULT_SQL_CONTEXT) == '"stored_balance">=0'
    callback.assert_called_once_with(Account)


@pytest.mark.asyncio
async def test_resolved_check_round_trip_uses_column_names(account_context: RakkoContext) -> None:
    state = ModelState.make_from_model("models", Account)
    constraint = state.options["constraints"][0]
    assert isinstance(constraint.check, SQLCriterion)
    path, args, kwargs = constraint.deconstruct()
    assert path == "rakko.migrations.constraints.CheckConstraint"
    restored = CheckConstraint(*args, **kwargs)
    assert restored == constraint
    assert hash(restored) == hash(constraint)
    assert restored.get_sql(Account, DEFAULT_SQL_CONTEXT) == '"stored_balance">=0'
    imports = ImportManager()
    source = render_value(kwargs["check"], imports)
    assert "stored_balance" in source
    assert "Account" not in source


def test_unresolved_check_is_not_evaluated_without_a_model() -> None:
    callback = Mock(return_value=Account.balance >= 0)
    constraint = CheckConstraint[Account](callback, "positive")
    assert constraint == CheckConstraint[Account](callback, "positive")
    assert hash(constraint) == hash(CheckConstraint[Account](callback, "positive"))
    with pytest.raises(ValueError, match="Resolve CheckConstraint"):
        constraint.deconstruct()
    callback.assert_not_called()


def test_check_rejects_invalid_callback_result() -> None:
    constraint = CheckConstraint[Account](Mock(return_value=True), "invalid")
    with pytest.raises(TypeError, match="Criterion"):
        constraint.resolve(Account)


@pytest.mark.asyncio
async def test_conditional_uniqueness_and_snapshot(account_context: RakkoContext) -> None:
    await account_context.generate_schemas()
    # Zero balances are outside the partial unique index.
    await Account.create(balance=0)
    await Account.create(balance=0)
    await Account.create(balance=1)
    with pytest.raises(IntegrityError):
        await Account.create(balance=1)
    with pytest.raises(IntegrityError):
        await Account.create(balance=-1)

    constraint = ModelState.make_from_model("models", Account).options["constraints"][1]
    path, args, kwargs = constraint.deconstruct()
    assert path == "rakko.migrations.constraints.UniqueConstraint"
    restored = UniqueConstraint(*args, **kwargs)
    assert restored == constraint
    assert hash(restored) == hash(constraint)
    assert restored.get_condition_sql(Account, DEFAULT_SQL_CONTEXT) == '"stored_balance">0'


def test_unique_callback_is_deferred_until_resolution() -> None:
    callback = Mock(return_value=Account.balance > 0)
    constraint = UniqueConstraint(fields=(Account.balance,), condition=callback)
    assert constraint == UniqueConstraint(fields=(Account.balance,), condition=callback)
    assert constraint != UniqueConstraint(fields=(Account.id,), condition=callback)
    assert hash(constraint) == hash(UniqueConstraint(fields=(Account.balance,), condition=callback))
    with pytest.raises(ValueError, match="Resolve UniqueConstraint"):
        constraint.deconstruct()
    callback.assert_not_called()


@pytest.mark.asyncio
async def test_unique_callback_receives_model(account_context: RakkoContext) -> None:
    callback = Mock(return_value=Account.balance > 0)
    constraint = UniqueConstraint(fields=(Account.balance,), condition=callback)
    assert constraint.get_condition_sql(Account, DEFAULT_SQL_CONTEXT) == '"stored_balance">0'
    callback.assert_called_once_with(Account)
    with pytest.raises(TypeError, match="Criterion"):
        UniqueConstraint(fields=(Account.balance,), condition=Mock(return_value=True)).resolve(
            Account
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("minimum", [0, 1])
async def test_check_diff_distinguishes_rename_from_changed_expression(
    account_context: RakkoContext,
    minimum: int,
) -> None:
    old_state = ModelState.make_from_model("models", Account)
    new_state = old_state.clone()
    new_state.options["constraints"] = (
        CheckConstraint[Account](lambda model: model.balance >= minimum, "renamed_balance").resolve(
            Account
        ),
        old_state.options["constraints"][1],
    )
    operations = StateModelDiff(old_state, new_state).generate_operations()
    if minimum == 0:
        assert len(operations) == 1
        assert isinstance(operations[0], RenameConstraint)
        assert operations[0].old_name == "positive_balance"
        assert operations[0].new_name == "renamed_balance"
    else:
        assert [type(operation) for operation in operations] == [RemoveConstraint, AddConstraint]


@pytest.mark.asyncio
@pytest.mark.parametrize("unresolved_side", ["old", "new"])
async def test_check_diff_rejects_unresolved_callbacks(
    account_context: RakkoContext,
    unresolved_side: str,
) -> None:
    old_state = ModelState.make_from_model("models", Account)
    new_state = old_state.clone()
    callback = Mock(return_value=Account.balance >= 0)
    state = old_state if unresolved_side == "old" else new_state
    state.options["constraints"] = (CheckConstraint(callback, "positive_balance"),)
    with pytest.raises(ValueError, match="must be resolved"):
        StateModelDiff(old_state, new_state).generate_operations()
    callback.assert_not_called()
