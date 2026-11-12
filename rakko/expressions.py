# Modified for Rakko ORM: replace Q filters with model-bound PyPika criteria and field expressions.

from __future__ import annotations

# PyPika returns concrete SQL nodes; these overrides return model-typed wrappers.
# pyright: reportIncompatibleMethodOverride=false
import inspect
import operator
from collections.abc import Callable, Iterable, Mapping
from copy import copy
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from enum import Enum
from functools import wraps
from typing import TYPE_CHECKING, Any, cast, overload

from pypika_tortoise import Case as PypikaCase
from pypika_tortoise import Field as PypikaField
from pypika_tortoise import SqlContext, Table
from pypika_tortoise.enums import Boolean, Equality
from pypika_tortoise.functions import DistinctOptionFunction, Floor
from pypika_tortoise.terms import (
    ArithmeticExpression,
    Array,
    BasicCriterion,
    ComplexCriterion,
    ContainsCriterion,
    Negative,
    NullValue,
    RangeCriterion,
    Term,
    Tuple,
    ValueWrapper,
)
from pypika_tortoise.terms import Criterion as PypikaCriterion
from pypika_tortoise.terms import Function as PypikaFunction
from pypika_tortoise.utils import format_alias_sql

from rakko.exceptions import FieldError
from rakko.fields.base import Field
from rakko.fields.data import JSONField
from rakko.fields.relational import RelationalField
from rakko.relations import reverse_relation

if TYPE_CHECKING:  # pragma: nocoverage
    from pypika_tortoise.queries import Selectable

    from rakko.filters import FilterInfoDict
    from rakko.models import Model
    from rakko.query_utils import TableCriterionTuple
    from rakko.queryset import AwaitableQuery


@dataclass(frozen=True)
class ResolveContext:
    model: type[Model]
    table: Table
    annotations: dict[str, Any]
    custom_filters: dict[str, FilterInfoDict]


@dataclass
class ResolveResult:
    term: Term
    joins: list[TableCriterionTuple] = dataclass_field(default_factory=list)
    output_field: Field | None = None


class Expression:
    """
    Parent class for expressions
    """

    def resolve(self, resolve_context: ResolveContext) -> ResolveResult:
        raise NotImplementedError()


class Value(Expression):
    """
    Wrapper for a value that should be used as a term in a query.
    """

    def __init__(self, value: Any) -> None:
        self.value = value

    def resolve(self, resolve_context: ResolveContext) -> ResolveResult:
        return ResolveResult(term=ValueWrapper(self.value))


class Connector(Enum):
    add = "add"
    sub = "sub"
    mul = "mul"
    div = "truediv"
    pow = "pow"
    mod = "mod"


class CombinedExpression(Expression):
    def __init__(self, left: Expression, connector: Connector, right: Any) -> None:
        self.left = left
        self.connector = connector
        self.right = right if isinstance(right, Expression) else Value(right)

    def resolve(self, resolve_context: ResolveContext) -> ResolveResult:
        left = self.left.resolve(resolve_context)
        right = self.right.resolve(resolve_context)
        left_output_field, right_output_field = left.output_field, right.output_field  # type: ignore

        if (
            left_output_field
            and right_output_field
            and type(left_output_field) is not type(right_output_field)
        ):
            raise FieldError("Cannot use arithmetic expression between different field type")

        operator_func = getattr(operator, self.connector.value)
        return ResolveResult(
            term=operator_func(left.term, right.term),
            joins=list(set(left.joins + right.joins)),  # dedup joins
            output_field=right_output_field or left_output_field,
        )


class F(Expression):
    """
    F() can be used to reference a model field, field of a related model, annotation or
    an attribute of a JSON field. It can be used in the following ways:

    - as a field reference, e.g. F("id")
    - as a related field reference, e.g. F("related_field__field") will return the value of the field
    of the related model.
    - as a JSON field reference, e.g. F("json_field__attribute") will return the value of the "attribute"
    property of the JSON field value. The reference can be nested, e.g. F("json_field__attribute__subattribute")
    - as a JSON field array element reference, e.g. F("json_field__0") will return the first element of the array.

    :param name: The name of the field to reference.
    """

    def __init__(self, name: str) -> None:
        self.name = name

    def resolve(self, resolve_context: ResolveContext) -> ResolveResult:
        term: Term
        joins: list[TableCriterionTuple] = []
        output_field = None

        from rakko.query_utils import resolve_field_json_path, resolve_nested_field

        main_name_part, __, rest_name_parts = self.name.partition("__")
        if main_name_part in resolve_context.model._meta.fetch_fields:
            # field in the format of "related_field__field" or "related_field__another_rel_field__field"
            term, joins, output_field = resolve_nested_field(
                resolve_context.model, resolve_context.table, self.name
            )
        elif (
            rest_name_parts
            and main_name_part in resolve_context.model._meta.fields_map
            and isinstance(resolve_context.model._meta.fields_map[main_name_part], JSONField)
        ):
            # Accessing a JSON field, e.g. F("json_field__a__b")
            key_parts = [
                int(item) if item.isdigit() else str(item) for item in rest_name_parts.split("__")
            ]
            term = resolve_field_json_path(
                PypikaField(resolve_context.model._meta.fields_db_projection[main_name_part]),
                key_parts,
            )
        elif self.name in resolve_context.annotations:
            # reference to another annotation, e.g. M.annotate(f1=...).annotate(f2=F("f1")).values('field')
            annotation = resolve_context.annotations[self.name]
            if isinstance(annotation, Term):
                term = annotation
            else:
                term = annotation.resolve(resolve_context).term
        else:
            # a regular model field, e.g. F("id")
            try:
                meta = resolve_context.model._meta
                term = PypikaField(meta.fields_db_projection[self.name])

                if (output_field := meta.fields_map.get(self.name, None)) and (
                    func := output_field.get_for_dialect(
                        meta.db.capabilities.dialect, "function_cast"
                    )
                ):
                    term = func(output_field, term)
            except KeyError:
                raise FieldError(
                    f"There is no non-virtual field {self.name} on Model {resolve_context.model.__name__}"
                ) from None
        return ResolveResult(term=term, output_field=output_field, joins=joins)

    def _combine(self, other: Any, connector: Connector, right_hand: bool) -> CombinedExpression:
        if not isinstance(other, Expression):
            other = Value(other)

        if right_hand:
            return CombinedExpression(other, connector, self)
        return CombinedExpression(self, connector, other)

    def __neg__(self) -> CombinedExpression:
        return self._combine(-1, Connector.mul, False)

    def __add__(self, other) -> CombinedExpression:
        return self._combine(other, Connector.add, False)

    def __sub__(self, other) -> CombinedExpression:
        return self._combine(other, Connector.sub, False)

    def __mul__(self, other) -> CombinedExpression:
        return self._combine(other, Connector.mul, False)

    def __truediv__(self, other) -> CombinedExpression:
        return self._combine(other, Connector.div, False)

    def __mod__(self, other) -> CombinedExpression:
        return self._combine(other, Connector.mod, False)

    def __pow__(self, other) -> CombinedExpression:
        return self._combine(other, Connector.pow, False)

    def __radd__(self, other) -> CombinedExpression:
        return self._combine(other, Connector.add, True)

    def __rsub__(self, other) -> CombinedExpression:
        return self._combine(other, Connector.sub, True)

    def __rmul__(self, other) -> CombinedExpression:
        return self._combine(other, Connector.mul, True)

    def __rtruediv__(self, other) -> CombinedExpression:
        return self._combine(other, Connector.div, True)

    def __rmod__(self, other) -> CombinedExpression:
        return self._combine(other, Connector.mod, True)

    def __rpow__(self, other) -> CombinedExpression:
        return self._combine(other, Connector.pow, True)


class Subquery(Term):
    def __init__(self, query: AwaitableQuery) -> None:
        super().__init__()
        self.query = query

    def get_sql(self, ctx: SqlContext) -> str:
        self.query._choose_db_if_not_chosen()
        self.query._make_query()
        return self.query.query.get_sql(ctx)

    def as_(self, alias: str) -> Selectable:  # type: ignore[override]
        self.query._choose_db_if_not_chosen()
        self.query._make_query()
        return self.query.query.as_(alias)


class RawSQL(Term):
    def __init__(self, sql: str) -> None:
        super().__init__()
        self.sql = sql

    def get_sql(self, ctx: SqlContext) -> str:
        if ctx.with_alias:
            return format_alias_sql(sql=self.sql, alias=self.alias, ctx=ctx)
        return self.sql


def _unwrap(value: Any) -> Any:
    if isinstance(value, (Query, Criterion)):
        return value.as_term()
    if isinstance(value, (list, tuple, set)):
        return type(value)(map(_unwrap, value))
    return value


def _inherit_operator(method: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(method)
    def operation(self, *args, **kwargs):
        term = _unwrap(method(self.as_term(), *map(_unwrap, args), **kwargs))
        return Criterion(term) if isinstance(term, PypikaCriterion) and not isinstance(term, PypikaFunction) else Query(term)

    return operation


class Criterion[M: Model](PypikaCriterion):
    """A PyPika condition carrying the model it is intended to filter."""

    def __init__(self, base: PypikaCriterion) -> None:
        super().__init__()
        self.base = base

    def as_term(self) -> PypikaCriterion:
        return self.base

    def nodes_(self):
        yield from self.base.nodes_()

    def get_sql(self, ctx: SqlContext) -> str:
        return self.base.get_sql(ctx)

    if TYPE_CHECKING:
        def __and__(self, other: Criterion[M]) -> Criterion[M]: ...
        def __or__(self, other: Criterion[M]) -> Criterion[M]: ...
        def __xor__(self, other: Criterion[M]) -> Criterion[M]: ...
        def __invert__(self) -> Criterion[M]: ...


for _name in ("__and__", "__or__", "__xor__", "__invert__", "negate"):
    setattr(Criterion, _name, _inherit_operator(getattr(PypikaCriterion, _name)))


class _BitwiseNot(Negative):
    def get_sql(self, ctx: SqlContext) -> str:
        return format_alias_sql(f'~({self.term.get_sql(ctx)})', self.alias, ctx)


def _field_path(field: Field, model: type[Model]) -> str:
    name = field.model_field_name
    if field.model is None or not name:
        raise FieldError("Expected a field bound to a model")
    if model._meta.fields_map.get(name) is field:
        return name
    relations = [
        relation_name
        for relation_name in model._meta.fetch_fields
        if isinstance(model._meta.fields_map[relation_name], RelationalField)
        and getattr(model._meta.fields_map[relation_name], "related_model") is field.model
    ]
    if len(relations) != 1:
        raise FieldError(f'Cannot unambiguously join {model.__name__} to {field.model.__name__}')
    return f'{relations[0]}__{name}'


type FieldReference = str | Query[Any, Any] | Field[Any] | reverse_relation[Any]


def field_name(value: FieldReference, model: type[Model], *, local: bool = False) -> str:
    """Resolve a field reference through the model's existing field metadata."""
    if isinstance(value, str):
        return value
    if isinstance(value, reverse_relation):
        if inspect.getattr_static(model, value.name, None) is not value:
            raise FieldError(f'Expected a relation belonging to {model.__name__}')
        relation = model._meta.fields_map.get(value.name)
        if not isinstance(relation, Field):
            raise FieldError(f'Relation {value.name!r} has not been initialized')
        value = relation
    while isinstance(value, Query):
        value = value.base
    if not isinstance(value, Field):
        raise FieldError("Expected a field reference")
    if local and model._meta.fields_map.get(value.model_field_name) is not value:
        raise FieldError(f'Expected a field belonging to {model.__name__}')
    return _field_path(value, model)


def field_values[K: FieldReference](values: Mapping[K, Any], model: type[Model]) -> dict[str, Any]:
    """Normalize model-value mappings without interpreting their values."""
    return {field_name(key, model, local=True): value for key, value in values.items()}


def ordering_name(value: Any, model: type[Model]) -> str:
    while isinstance(value, Query):
        value = value.base
    prefix = ""
    if isinstance(value, Negative):
        prefix, value = '-', value.term
    while isinstance(value, Query):
        value = value.base
    if not isinstance(value, Field):
        raise FieldError("Ordering requires a field or a signed field")
    return prefix + field_name(value, model)


def _resolve_field(field: Field, context: ResolveContext) -> ResolveResult:
    from rakko.fields.relational import (
        ForeignKeyFieldInstance,
        OneToOneFieldInstance,
    )

    name = field.model_field_name
    if context.model._meta.fields_map.get(name) is field:
        if isinstance(field, (ForeignKeyFieldInstance, OneToOneFieldInstance)):
            name = field.source_field
        if name not in context.model._meta.fields_db_projection:
            raise FieldError(f'Field {field.model_field_name!r} has no database column')
        output_field = context.model._meta.fields_map[name]
        term = context.table[context.model._meta.fields_db_projection[name]]
        function_cast = output_field.get_for_dialect(
            context.model._meta.db.capabilities.dialect, "function_cast"
        )
        if function_cast is not None:
            term = function_cast(output_field, term)
        return ResolveResult(term=term, output_field=output_field)

    from rakko.query_utils import resolve_nested_field

    term, joins, output_field = resolve_nested_field(
        context.model, context.table, _field_path(field, context.model)
    )
    return ResolveResult(term=term, joins=joins, output_field=output_field)


def resolve_term(value: Any, context: ResolveContext) -> ResolveResult:
    """Bind a native expression tree to ORM columns without mutating the source."""
    from rakko.fields.base import Field
    from rakko.models import Model

    fields: dict[int, ResolveResult] = {}

    def resolve(value: Any, field: Field | None = None) -> ResolveResult:
        if isinstance(value, Field):
            if id(value) not in fields:
                fields[id(value)] = _resolve_field(value, context)
            return fields[id(value)]
        if isinstance(value, (Query, Criterion)):
            return resolve(value.base)
        if isinstance(value, Expression):
            return value.resolve(context)
        if isinstance(value, ValueWrapper):
            result = copy(value)
            literal = value.value
            if isinstance(literal, Model):
                reference = getattr(field, "reference", None)
                if reference is not None and not isinstance(literal, reference.related_model):
                    raise FieldError(
                        f'Expected a {reference.related_model.__name__} relation value'
                    )
                literal = (
                    getattr(literal, reference.to_field_instance.model_field_name)
                    if reference
                    else literal.pk
                )
                if literal is None:
                    raise FieldError(
                        "A related model must have a key before it can be used in a condition"
                    )
            result.value = (
                field.to_db_value(literal, context.model) if field is not None else literal
            )
            return ResolveResult(result)
        if not isinstance(value, Term):
            return ResolveResult(ValueWrapper(value))

        result = ResolveResult(copy(value))
        bound_field = field if isinstance(value, (Tuple, Array)) else None
        left_name = (
            "left"
            if isinstance(value, BasicCriterion) and not isinstance(value, ComplexCriterion)
            else "term"
        )
        if isinstance(
            value, (BasicCriterion, ContainsCriterion, RangeCriterion)
        ) and not isinstance(value, ComplexCriterion):
            left = resolve(getattr(value, left_name))
            setattr(result.term, left_name, left.term)
            result.joins.extend(left.joins)
            bound_field = getattr(left, "output_field")
            setattr(result, "output_field", bound_field)
        else:
            left_name = ""

        def visit(item: Any) -> Any:
            if isinstance(item, (Term, Expression)):
                child = resolve(item, bound_field)
                result.joins.extend(child.joins)
                if getattr(result, "output_field") is None:
                    setattr(result, "output_field", getattr(child, "output_field"))
                return child.term
            if isinstance(item, (list, tuple)):
                return type(item)(map(visit, item))
            return item

        for name, item in vars(value).items():
            if name != left_name:
                setattr(result.term, name, visit(item))
        term = result.term
        if (
            isinstance(term, BasicCriterion)
            and not isinstance(term, ComplexCriterion)
            and isinstance(term.right, NullValue)
        ):
            if term.comparator not in {Equality.eq, Equality.ne}:
                raise ValueError("NULL supports only equality and inequality comparisons")
            result.term = (
                term.left.isnull() if term.comparator is Equality.eq else term.left.notnull()
            )
        elif (
            isinstance(term, ContainsCriterion)
            and isinstance(term.container, Tuple)
            and not term.container.values
        ):
            result.term = ValueWrapper(1) == int(term._is_negated)
        elif isinstance(term, ComplexCriterion) and term.comparator is Boolean.xor_:
            left, right = cast(Criterion, term.left), cast(Criterion, term.right)
            result.term = (left & ~right) | (~left & right)
        elif type(term) is Negative:
            result.term = -1 * term.term
        return result

    return resolve(value)


class Query[M: Model, T](Term, Expression):
    """A typed descriptor around a native PyPika term."""

    __hash__ = object.__hash__

    if TYPE_CHECKING:
        def __pos__(self) -> Query[M, T]: ...
        def __neg__(self) -> Query[M, T]: ...
        def __add__(self, other: T | Query[M, T]) -> Query[M, T]: ...
        def __radd__(self, other: T | Query[M, T]) -> Query[M, T]: ...
        def __sub__(self, other: T | Query[M, T]) -> Query[M, T]: ...
        def __rsub__(self, other: T | Query[M, T]) -> Query[M, T]: ...
        def __mul__(self, other: T | Query[M, T]) -> Query[M, T]: ...
        def __rmul__(self, other: T | Query[M, T]) -> Query[M, T]: ...
        def __truediv__(self, other: T | Query[M, T]) -> Query[M, T]: ...
        def __rtruediv__(self, other: T | Query[M, T]) -> Query[M, T]: ...
        def __pow__(self, other: T | Query[M, T]) -> Query[M, T]: ...
        def __mod__(self, other: T | Query[M, T]) -> Query[M, T]: ...
        def __rmod__(self, other: T | Query[M, T]) -> Query[M, T]: ...
        def __floordiv__(self, other: T | Query[M, T]) -> Query[M, T]: ...
        def __rfloordiv__(self, other: T | Query[M, T]) -> Query[M, T]: ...
        def __eq__(self, other: T | Query[M, T]) -> Criterion[M]: ...
        def __ne__(self, other: T | Query[M, T]) -> Criterion[M]: ...
        def __gt__(self, other: T | Query[M, T]) -> Criterion[M]: ...
        def __lt__(self, other: T | Query[M, T]) -> Criterion[M]: ...
        def __ge__(self, other: T | Query[M, T]) -> Criterion[M]: ...
        def __le__(self, other: T | Query[M, T]) -> Criterion[M]: ...
        def like(self, pattern: str) -> Criterion[M]: ...
        def not_like(self, pattern: str) -> Criterion[M]: ...
        def ilike(self, pattern: str) -> Criterion[M]: ...
        def not_ilike(self, pattern: str) -> Criterion[M]: ...
        def regex(self, pattern: str) -> Criterion[M]: ...
        def between(self, lower: T | Query[M, T], upper: T | Query[M, T]) -> Criterion[M]: ...
        def isnull(self) -> Criterion[M]: ...
        def notnull(self) -> Criterion[M]: ...

    def isin(self, values: Iterable[T | Query[M, T]] | Term) -> Criterion[M]:
        return _inherit_operator(Term.isin)(self, list(values) if not isinstance(values, Term) else values)

    def notin(self, values: Iterable[T | Query[M, T]] | Term) -> Criterion[M]:
        return _inherit_operator(lambda term, values: Term.isin(term, values).negate())(
            self, list(values) if not isinstance(values, Term) else values
        )

    def __invert__(self) -> Query[M, T]:
        return Query(_BitwiseNot(self.as_term()))



    def __init__(self, base: Any) -> None:
        super().__init__()
        self.base = base.base if isinstance(base, Query) else base

    def as_term(self) -> Term:
        return self.base if isinstance(self.base, Term) else self

    @overload
    def __get__(self, instance: None, owner: type[M]) -> Query[M, T]: ...

    @overload
    def __get__(self, instance: M, owner: type[M]) -> T: ...

    def __get__(self, instance: M | None, owner: type[M]) -> Query[M, T] | T:
        return self if instance is None else getattr(instance, self.base.model_field_name)

    def __set__(self, instance: M, value: T) -> None:
        setattr(instance, self.base.model_field_name, value)

    def __str__(self) -> str:
        return str(self.base)

    def get_sql(self, ctx: SqlContext) -> str:
        return self.base.model_field_name if isinstance(self.base, Field) else self.base.get_sql(ctx)

    def resolve(self, resolve_context: ResolveContext) -> ResolveResult:
        return resolve_term(self.base, resolve_context)

    @property
    def sql(self) -> str:
        from rakko.fields.base import Field

        term = self.base.term if isinstance(self.base, Negative) else self.base
        field = next(node.base for node in term.nodes_() if isinstance(node, Query) and isinstance(node.base, Field))
        model = cast("type[M]", field.model)
        return self.resolve(ResolveContext(model, model._meta.basetable, {}, {})).term.get_sql(
            model._meta.db.query_class.SQL_CONTEXT
        )


# Adapt only return types; PyPika builds the expression trees.
for _name in (
    "__pos__ __neg__ __add__ __radd__ __sub__ __rsub__ __mul__ __rmul__ "
    "__truediv__ __rtruediv__ __pow__ __mod__ __eq__ __ne__ __gt__ __lt__ __ge__ __le__ "
    "eq ne gt gte lt lte like not_like ilike not_ilike regex rlike bin_regex glob "
    "between isnull notnull as_"
).split():
    setattr(Query, _name, _inherit_operator(getattr(Term, _name)))
Query.__floordiv__ = _inherit_operator(lambda left, right: Floor(left / right))
Query.__rfloordiv__ = _inherit_operator(lambda left, right: Floor(right / left))
Query.__rmod__ = _inherit_operator(lambda left, right: right % left)
Query.notnull = _inherit_operator(lambda term: Term.isnull(term).negate())


def _process_filter_kwarg(
    model: type[Model], key: str, value: Any, table: Table
) -> tuple[PypikaCriterion, tuple[Table, PypikaCriterion] | None]:
    join = None

    if value is None and f"{key}__isnull" in model._meta.filters:
        filter_info = model._meta.get_filter(f"{key}__isnull")
        value = True
    else:
        filter_info = model._meta.get_filter(key)

    field_object = None
    if "table" in filter_info:
        # join the table
        join = (
            filter_info["table"],
            table[model._meta.db_pk_column]
                == filter_info["table"][filter_info.get("backward_key", "")],
        )
        if "value_encoder" in filter_info:
            value = filter_info["value_encoder"](value, model)
        table = filter_info["table"]
    elif not isinstance(value, Term):
        field_object = model._meta.fields_map[filter_info["field"]]
        value = (
            filter_info["value_encoder"](value, model, field_object)
            if "value_encoder" in filter_info
            else field_object.to_db_value(value, model)
        )
    op = filter_info["operator"]
    term: Term = table[filter_info.get("source_field", filter_info["field"])]
    if field_object is not None:
        func = field_object.get_for_dialect(
            model._meta.db.capabilities.dialect, "function_cast"
        )
        if func is not None:
            term = func(field_object, term)
    criterion = op(term, value)
    return criterion, join


def _get_actual_filter_params(
    resolve_context: ResolveContext, key: str, value: Any
) -> tuple[str, Any]:
    from rakko.fields.relational import RelationalField

    filter_key = key
    filter_value: Any
    model_meta = resolve_context.model._meta
    relation_name, separator, lookup = key.partition("__")
    if (
        (relation_name in model_meta.fk_fields or relation_name in model_meta.o2o_fields)
        and (not separator or lookup in ("in", "not_in"))
        and (
            # Keep bare relation conversion (e.g. `filter(tournament=obj)`), but
            # let exact field or annotation names win over relation lookups. e.g.
            #
            #     .annotate(tournament__in=F("id")).filter(tournament__in=relation.pk)
            #
            # Here `tournament__in` refers to the annotation, not the FK lookup.
            not lookup
            or (key not in model_meta.filters and key not in resolve_context.custom_filters)
        )
    ):
        field_object = cast(RelationalField, model_meta.fields_map[relation_name])
        filter_key = cast(str, field_object.source_field)
        to_field_name = field_object.to_field_instance.model_field_name
        if lookup:
            filter_key = f"{filter_key}__{lookup}"
            filter_value = (
                value
                if isinstance(value, (Expression, Term))
                else [
                    getattr(item, to_field_name)
                    if isinstance(item, field_object.related_model)
                    else item
                    for item in value
                ]
            )
        else:
            filter_value = (
                getattr(value, to_field_name)
                if isinstance(value, field_object.related_model)
                else value
            )
    elif key in model_meta.m2m_fields:
        filter_value = getattr(value, "pk", value)
    elif (
        relation_name in model_meta.fetch_fields
        or key in resolve_context.custom_filters
        or key in model_meta.filters
    ):
        filter_value = value
    else:
        allowed = sorted(
            model_meta.fields | model_meta.fetch_fields | set(resolve_context.custom_filters)
        )
        raise FieldError(f"Unknown filter param '{key}'. Allowed base values are {allowed}")

    if isinstance(filter_value, (Expression, Term)):
        filter_value = resolve_term(filter_value, resolve_context).term

    return filter_key, filter_value


def resolve_filter(context: ResolveContext, key: str, value: Any) -> ResolveResult:
    """Compile a keyword lookup directly to a PyPika criterion."""
    key, value = _get_actual_filter_params(context, key, value)
    if key in context.custom_filters:
        info = context.custom_filters[key]
        result = resolve_term(context.annotations[info["field"]], context)
        operation = context.model._meta.db.executor_class.get_overridden_filter_func(
            filter_func=info["operator"], filter_info=info
        ) or info["operator"]
        return ResolveResult(operation(result.term, value), result.joins)

    relation_name, _, lookup = key.partition("__")
    if key not in context.model._meta.filters and relation_name in context.model._meta.fetch_fields:
        from rakko.query_utils import get_joins_for_related_field

        relation = cast(RelationalField, context.model._meta.fields_map[relation_name])
        joins = get_joins_for_related_field(context.table, relation, relation_name)
        result = resolve_filter(
            ResolveContext(relation.related_model, joins[-1][0], context.annotations, context.custom_filters),
            lookup, value,
        )
        return ResolveResult(result.term, joins + result.joins)

    criterion, join = _process_filter_kwarg(context.model, key, value, context.table)
    return ResolveResult(criterion, [join] if join else [])


class Function(Expression):
    """
    Function/Aggregate base.

    :param field: Field name
    :param default_values: Extra parameters to the function.

    .. attribute:: database_func
        :annotation: pypika_tortoise.terms.Function

        The pypika function this represents.

    .. attribute:: populate_field_object
        :annotation: bool = False

        Enable populate_field_object where we want to try and preserve the field type.
    """

    __slots__ = ("default_values", "field", "field_object")

    database_func: Callable[..., PypikaFunction] = PypikaFunction
    # Enable populate_field_object where we want to try and preserve the field type.
    populate_field_object = False

    def __init__(
        self, field: str | Expression | Term, *default_values: Any
    ) -> None:
        self.field = field
        self.field_object: Field | None = None
        self.default_values = default_values

    def _get_function_field(self, field: Term | str, *default_values) -> PypikaFunction:
        return self.database_func(field, *default_values)  # type:ignore

    def _resolve_nested_field(self, resolve_context: ResolveContext, field: str) -> ResolveResult:
        from rakko.query_utils import resolve_nested_field

        term, joins, output_field = resolve_nested_field(
            resolve_context.model, resolve_context.table, field
        )
        if self.populate_field_object:
            self.field_object = output_field
        return ResolveResult(term=term, joins=joins, output_field=output_field)

    def _resolve_argument(
        self, resolve_context: ResolveContext, value: Any, *, treat_str_as_field: bool
    ) -> ResolveResult:
        if isinstance(value, Expression):
            return value.resolve(resolve_context)
        if isinstance(value, Term):
            return resolve_term(value, resolve_context)
        if isinstance(value, str) and treat_str_as_field:
            return self._resolve_nested_field(resolve_context, value)
        return ResolveResult(term=cast(Term, value))

    def resolve(self, resolve_context: ResolveContext) -> ResolveResult:
        """
        Used to resolve the Function statement for SQL generation.

        :param model: Model the function is applied on to.
        :param table: ``pypika_tortoise.Table`` to keep track of the virtual SQL table
            (to allow self referential joins)
        :return: Dict with keys ``"joins"`` and ``"fields"``
        """

        function_arg = self._resolve_argument(resolve_context, self.field, treat_str_as_field=True)
        resolved_defaults = [
            self._resolve_argument(resolve_context, value, treat_str_as_field=False)
            for value in self.default_values
        ]
        default_terms = [value.term for value in resolved_defaults]
        term = self._get_function_field(function_arg.term, *default_terms)
        joins = function_arg.joins
        for value in resolved_defaults:
            if value.joins:
                joins = list(set(joins + value.joins))
        res = ResolveResult(
            term=term,
            joins=joins,
            output_field=function_arg.output_field,  # type:ignore
        )

        if self.populate_field_object and (
            res_output_field := res.output_field  # type:ignore
        ):
            self.field_object = res_output_field

        return res


class Aggregate(Function):
    """
    Base for SQL Aggregates.

    :param field: Field name
    :param default_values: Extra parameters to the function.
    :param distinct: Flag for aggregate with distinction
    """

    database_func: Callable[..., PypikaFunction] = DistinctOptionFunction

    def __init__(
        self,
        field: str | Expression | Term,
        *default_values: Any,
        distinct: bool = False,
        _filter: Criterion | None = None,
    ) -> None:
        super().__init__(field, *default_values)
        self.distinct = distinct
        self.filter = _filter

    def _get_function_field(  # type:ignore
        self, field: ArithmeticExpression | PypikaField | str, *default_values
    ) -> DistinctOptionFunction:
        function = cast(DistinctOptionFunction, self.database_func(field, *default_values))
        if self.distinct:
            return function.distinct()
        return function

    def _resolve_argument(
        self, resolve_context: ResolveContext, value: Any, *, treat_str_as_field: bool
    ) -> ResolveResult:
        ret = super()._resolve_argument(
            resolve_context, value, treat_str_as_field=treat_str_as_field
        )
        # Only the aggregated argument is filtered, whether it is a field name,
        # an F() or a combined expression; extra function arguments are left as is.
        if treat_str_as_field and self.filter is not None:
            condition = resolve_term(self.filter, resolve_context)
            ret.term = PypikaCase().when(condition.term, ret.term).else_(None)
            ret.joins = list(dict.fromkeys(ret.joins + condition.joins))

        return ret


class _WhenThen(Term):
    """This is not a real term, but a helper to store the when and then terms."""

    def __init__(self, when: Term, then: Term) -> None:
        self.when = when
        self.then = then


class When(Expression):
    """
    When expression.

    :param args: PyPika criteria
    :param kwargs: keyword criterion like filter
    :param then: value for criterion
    :param negate: false (default)
    """

    def __init__(
        self,
        *args: Criterion,
        then: str | bool | float | F | CombinedExpression | Function,
        negate: bool = False,
        **kwargs: Any,
    ) -> None:
        if not all(isinstance(criterion, Criterion) for criterion in args):
            raise TypeError("Expected PyPika Criterion arguments")
        self.args = args
        self.then = then
        self.negate = negate
        self.kwargs = kwargs

    def resolve(self, resolve_context: ResolveContext) -> ResolveResult:
        conditions = []
        joins = []
        for criterion in self.args:
            result = resolve_term(criterion, resolve_context)
            conditions.append(~result.term if self.negate else result.term)
            joins.extend(result.joins)
        for key, value in self.kwargs.items():
            result = resolve_filter(resolve_context, key, value)
            conditions.append(~result.term if self.negate else result.term)
            joins.extend(result.joins)
        then = resolve_term(self.then, resolve_context)
        return ResolveResult(
            term=_WhenThen(cast(Term, Criterion.all(conditions)), then.term),
            joins=list(dict.fromkeys(joins + then.joins)),
        )


class Case(Expression):
    """
    Case expression.

    :param args: When objects
    :param default: value for 'CASE WHEN ... THEN ... ELSE <default> END'
    """

    def __init__(
        self,
        *args: When,
        default: str | bool | float | F | CombinedExpression | Function | None = None,
    ) -> None:
        self.args = args
        self.default = default

    def resolve(self, resolve_context: ResolveContext) -> ResolveResult:
        case = PypikaCase()
        joins: list[TableCriterionTuple] = []
        for arg in self.args:
            if not isinstance(arg, When):
                raise TypeError("expected When objects as args")
            when = arg.resolve(resolve_context)
            when_term = cast(_WhenThen, when.term)
            case = case.when(when_term.when, when_term.then)
            joins += when.joins

        if isinstance(self.default, Expression):
            default_result = self.default.resolve(resolve_context)
            joins += default_result.joins
            case = case.else_(default_result.term)
        else:
            case = case.else_(Term.wrap_constant(self.default))

        return ResolveResult(term=case, joins=list(dict.fromkeys(joins)))
