# Modified for Rakko ORM: accept expression conditions and field-reference unique constraints.

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


type Condition[M: Model] = Criterion | Callable[[type[M]], Criterion]


def _condition[M: Model](value: Condition[M], model: type[M]) -> Criterion:
    value = value(model) if callable(value) else value
    if not isinstance(value, Criterion):
        raise TypeError("Constraint conditions require a Criterion or a callable returning one")
    return value


def _resolve_condition[M: Model](value: Condition[M], model: type[M]) -> Criterion:
    from rakko.expressions import ResolveContext, resolve_term

    result = resolve_term(
        _condition(value, model),
        ResolveContext(
            model=model,
            table=model.get_table(),
            annotations={},
            custom_filters=model._meta.filters,
        ),
    )
    if result.joins:
        raise ValueError("Constraint conditions cannot reference joined models")

    return cast(Criterion, result.term)


def _condition_signature[M: Model](
    value: Condition[M],
) -> str | Callable[[type[M]], Criterion]:
    # Callbacks cannot be evaluated until a model is supplied to resolve().
    return value.get_sql(DEFAULT_SQL_CONTEXT) if isinstance(value, Criterion) else value


def _deconstruct_condition(value: Condition, constraint_name: str) -> Criterion:
    if callable(value):
        raise ValueError(f"Resolve {constraint_name} with a model before deconstructing it")
    return value


@dataclass(frozen=True, eq=False)
class UniqueConstraint:
    """Require unique field combinations, optionally for a subset of rows.

    ``condition`` accepts a Criterion or a callback receiving the model class.
    Conditional uniqueness is implemented as a partial unique index and is
    supported only by the PostgreSQL and SQLite backends. Other backends,
    including MySQL, raise NotImplementedError when generating its SQL.
    Unconditional unique constraints do not have this backend restriction.

    Call resolve(model) before serializing a constraint with a callback.
    """

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
                _resolve_condition(self.condition, model) if self.condition is not None else None
            ),
        )

    def _signature(self) -> tuple:
        from rakko.expressions import Query

        # Query comparisons build SQL expressions rather than boolean equality.
        fields = tuple(
            value
            if isinstance(value, str)
            else id(value.base if isinstance(value, Query) else value)
            for value in self.fields
        )
        return (
            fields,
            self.name,
            _condition_signature(self.condition) if self.condition is not None else None,
        )

    def get_condition_sql(self, model: type[Model], context: SqlContext) -> str:
        condition = self.resolve(model).condition
        if condition is None:
            raise ValueError("This unique constraint has no condition")
        return cast(Criterion, condition).get_sql(context)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, UniqueConstraint) and self._signature() == other._signature()

    def __hash__(self) -> int:
        return hash(self._signature())

    def deconstruct(self) -> tuple[str, list, dict]:
        path = f"{self.__class__.__module__}.{self.__class__.__name__}"
        kwargs: dict = {"fields": self.fields, "name": self.name}
        if self.condition is not None:
            kwargs["condition"] = _deconstruct_condition(self.condition, "UniqueConstraint")
        return path, [], kwargs


@dataclass(frozen=True, eq=False)
class CheckConstraint[M: Model]:
    """Require every row to satisfy a Criterion or a model-class callback.

    Callbacks receive the model class when resolve(model) or get_sql(model,
    context) is called. Call resolve(model) before serializing a callback.
    """

    check: Condition[M]
    name: str

    def __post_init__(self) -> None:
        if not (isinstance(self.check, Criterion) or callable(self.check)):
            raise TypeError("CheckConstraint.check requires a Criterion")

    def resolve(self, model: type[M]) -> CheckConstraint[M]:
        return CheckConstraint(check=_resolve_condition(self.check, model), name=self.name)

    def get_sql(self, model: type[M], context: SqlContext) -> str:
        return cast(Criterion, self.resolve(model).check).get_sql(context)

    def _signature(self) -> tuple[str, str | Callable[[type[M]], Criterion]]:
        return self.name, _condition_signature(self.check)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, CheckConstraint) and self._signature() == other._signature()

    def __hash__(self) -> int:
        return hash(self._signature())

    def deconstruct(self) -> tuple[str, list, dict]:
        path = f"{self.__class__.__module__}.{self.__class__.__name__}"
        return (
            path,
            [],
            {
                "check": _deconstruct_condition(self.check, "CheckConstraint"),
                "name": self.name,
            },
        )
