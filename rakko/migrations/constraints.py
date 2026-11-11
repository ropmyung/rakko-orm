# Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
# Derived from Tortoise ORM; maintained and modified for Rakko ORM.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from pypika_tortoise.context import DEFAULT_SQL_CONTEXT
from pypika_tortoise.terms import Criterion

if TYPE_CHECKING:
    from pypika_tortoise.context import SqlContext

    from rakko.expressions import FieldReference
    from rakko.models import Model


type Condition = Criterion | Callable[[], Criterion]


def _condition(value: Condition) -> Criterion:
    value = value() if callable(value) else value
    if not isinstance(value, Criterion):
        raise TypeError("Constraint conditions require a Criterion or a callable returning one")
    return value


def _resolve_condition(value: Condition, model: type[Model]) -> Criterion:
    from rakko.expressions import ResolveContext, resolve_term

    result = resolve_term(
        _condition(value),
        ResolveContext(
            model=model, table=model.get_table(), annotations={},
            custom_filters=model._meta.filters,
        ),
    )
    if result.joins:
        raise ValueError("Constraint conditions cannot reference joined models")

    return cast(Criterion, result.term)


@dataclass(frozen=True, eq=False)
class UniqueConstraint:
    fields: tuple[FieldReference, ...]
    name: str | None = None
    condition: Condition | None = None

    def __post_init__(self) -> None:
        if self.condition is not None and not (
            isinstance(self.condition, Criterion) or callable(self.condition)
        ):
            raise TypeError("UniqueConstraint.condition requires a Criterion")

    def resolve(self, model: type[Model]) -> UniqueConstraint:
        from rakko.expressions import field_name

        return UniqueConstraint(
            fields=tuple(field_name(value, model, local=True) for value in self.fields),
            name=self.name,
            condition=(
                _resolve_condition(self.condition, model)
                if self.condition is not None else None
            ),
        )

    def _signature(self) -> tuple:
        return (
            self.fields, self.name,
            _condition(self.condition).get_sql(DEFAULT_SQL_CONTEXT)
            if self.condition is not None else None,
        )

    def get_condition_sql(self, model: type[Model], context: SqlContext) -> str:
        condition = self.resolve(model).condition
        if condition is None:
            raise ValueError("This unique constraint has no condition")
        return _condition(condition).get_sql(context)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, UniqueConstraint) and self._signature() == other._signature()

    def __hash__(self) -> int:
        return hash(self._signature())

    def deconstruct(self) -> tuple[str, list, dict]:
        path = f'{self.__class__.__module__}.{self.__class__.__name__}'
        kwargs: dict = {"fields": self.fields, "name": self.name}
        if self.condition is not None:
            kwargs["condition"] = _condition(self.condition)
        return path, [], kwargs


@dataclass(frozen=True, eq=False)
class CheckConstraint:
    check: Condition
    name: str

    def __post_init__(self) -> None:
        if not (isinstance(self.check, Criterion) or callable(self.check)):
            raise TypeError("CheckConstraint.check requires a Criterion")

    def resolve(self, model: type[Model]) -> CheckConstraint:
        return CheckConstraint(check=_resolve_condition(self.check, model), name=self.name)

    def get_sql(self, model: type[Model], context: SqlContext) -> str:
        return _condition(self.resolve(model).check).get_sql(context)

    def _signature(self) -> tuple[str, str]:
        return self.name, _condition(self.check).get_sql(DEFAULT_SQL_CONTEXT)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, CheckConstraint) and self._signature() == other._signature()

    def __hash__(self) -> int:
        return hash(self._signature())

    def deconstruct(self) -> tuple[str, list, dict]:
        path = f'{self.__class__.__module__}.{self.__class__.__name__}'
        return path, [], {"check": _condition(self.check), "name": self.name}
