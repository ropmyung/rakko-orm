# Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
# Derived from Tortoise ORM; maintained and modified for Rakko ORM.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import operator
from collections.abc import Callable, Sequence
from copy import copy
from typing import TYPE_CHECKING, Any, cast

from pypika_tortoise import Table
from pypika_tortoise.terms import (
    Criterion,
    JSONAttributeCriterion,
    Term,
)

from rakko.exceptions import FieldError, OperationalError
from rakko.fields.base import Field
from rakko.fields.relational import (
    BackwardFKRelation,
    ForeignKeyFieldInstance,
    ManyToManyFieldInstance,
    RelationalField,
)

if TYPE_CHECKING:  # pragma: nocoverage
    from rakko.expressions import FieldReference
    from rakko.models import Model
    from rakko.queryset import QuerySet


TableCriterionTuple = tuple[Table, Criterion]


def get_joins_for_related_field(
    table: Table, related_field: RelationalField, related_field_name: str
) -> list[TableCriterionTuple]:
    required_joins: list[TableCriterionTuple] = []

    related_table: Table = related_field.related_model._meta.basetable
    if isinstance(related_field, ManyToManyFieldInstance):
        through_table = Table(related_field.through, schema=related_field.through_schema)
        related_table = related_table.as_(f"{table.get_table_name()}__{related_field_name}")
        required_joins.append(
            (
                through_table,
                table[related_field.model._meta.db_pk_column]
                == through_table[related_field.backward_key],
            )
        )
        required_joins.append(
            (
                related_table,
                through_table[related_field.forward_key]
                == related_table[related_field.related_model._meta.db_pk_column],
            )
        )
    elif isinstance(related_field, BackwardFKRelation):
        to_field_source_field = (
            related_field.to_field_instance.source_field
            or related_field.to_field_instance.model_field_name
        )

        if table == related_table:
            related_table = related_table.as_(f"{table.get_table_name()}__{related_field_name}")
        required_joins.append(
            (
                related_table,
                table[to_field_source_field] == related_table[related_field.relation_source_field],
            )
        )
    else:
        to_field_source_field = (
            related_field.to_field_instance.source_field
            or related_field.to_field_instance.model_field_name
        )

        from_field = related_field.model._meta.fields_map[related_field.source_field]  # type: ignore
        from_field_source_field = from_field.source_field or from_field.model_field_name

        related_table = related_table.as_(f"{table.get_table_name()}__{related_field_name}")
        required_joins.append(
            (
                related_table,
                related_table[to_field_source_field] == table[from_field_source_field],
            )
        )
    return required_joins


def expand_lookup_expression(root_model: type[Model], lookup_expression: str) -> Sequence[Field]:
    field_names = lookup_expression.split("__")
    fields: list[Field | RelationalField] = []
    model = root_model
    for field_name in field_names[:-1]:
        if field_name not in model._meta.fetch_fields:
            raise FieldError(f"{lookup_expression} not resolvable")
        field = cast(RelationalField, model._meta.fields_map[field_name])
        fields.append(field)
        model = field.related_model
    # the last field is not necessarily a RelationalField, so threting it differently
    try:
        fields.append(model._meta.fields_map[field_names[-1]])
    except KeyError:
        raise FieldError(f"{lookup_expression} not resolvable")
    return fields


def resolve_nested_field(
    model: type[Model], table: Table, field: str
) -> tuple[Term, list[TableCriterionTuple], Field | None]:
    """
    Resolves a nested field string like events__participants__name and
    returns the pypika term, required joins and the Field that can be used for
    converting the value.
    """
    joins = []
    fields = expand_lookup_expression(model, field)

    for iter_field in fields[:-1]:
        related_field = cast(RelationalField, iter_field)
        joins.extend(get_joins_for_related_field(table, related_field, iter_field.model_field_name))

        model = related_field.related_model
        related_table: Table = related_field.related_model._meta.basetable
        if isinstance(related_field, (ForeignKeyFieldInstance, ManyToManyFieldInstance)):
            related_table = related_table.as_(
                f"{table.get_table_name()}__{iter_field.model_field_name}"
            )
        table = related_table

    last_field = fields[-1]
    if last_field.model_field_name in model._meta.fetch_fields:
        related_field = cast(RelationalField, last_field)
        related_field_meta = related_field.related_model._meta

        joins.extend(
            get_joins_for_related_field(table, related_field, related_field.model_field_name)
        )
        related_table = related_field_meta.basetable

        if isinstance(related_field, BackwardFKRelation):
            if table == related_table:
                related_table = related_table.as_(
                    f"{table.get_table_name()}__{related_field.model_field_name}"
                )
        elif isinstance(related_field, ManyToManyFieldInstance):
            related_table = related_table.as_(
                f"{table.get_table_name()}__{related_field.model_field_name}"
            )

        term = related_table[related_field_meta.db_pk_column]
    else:
        if last_field.source_field:
            term = table[last_field.source_field]
        else:
            term = table[last_field.model_field_name]

        if last_field:  # pragma: nobranch
            func = last_field.get_for_dialect(model._meta.db.capabilities.dialect, "function_cast")
            if func:
                term = func(last_field, term)

    return term, joins, last_field


class Prefetch:
    """
    Prefetcher container. One would directly use this when wanting to attach a custom QuerySet
    for specialised prefetching.

    :param relation: Related field name.
    :param queryset: Custom QuerySet to use for prefetching.
    :param to_attr: Sets the result of the prefetch operation to a custom attribute.
    """

    __slots__ = ("relation", "queryset", "to_attr")

    def __init__(self, relation: FieldReference, queryset: QuerySet, to_attr: str | None = None) -> None:
        self.to_attr = to_attr
        self.relation = relation
        self.queryset = queryset
        self.queryset.query = copy(self.queryset.model._meta.basequery)

    def resolve_for_queryset(self, queryset: QuerySet) -> None:
        """
        Called internally to generate prefetching query.

        :param queryset: Custom QuerySet to use for prefetching.
        :raises OperationalError: If field does not exist in model.
        """

        from rakko.expressions import field_name

        first_level_field, __, forwarded_prefetch = field_name(
            self.relation, queryset.model
        ).partition("__")
        if first_level_field not in queryset.model._meta.fetch_fields:
            raise OperationalError(
                f"relation {first_level_field} for {queryset.model._meta.db_table} not found"
            )

        if forwarded_prefetch:
            if first_level_field not in queryset._prefetch_map:
                queryset._prefetch_map[first_level_field] = set()
            queryset._prefetch_map[first_level_field].add(
                Prefetch(forwarded_prefetch, self.queryset, to_attr=self.to_attr)
            )
        else:
            queryset._prefetch_queries.setdefault(first_level_field, []).append(
                (self.to_attr, self.queryset)
            )


def get_json_filter_operator(
    value: dict[str, Any], operator_keywords: dict[str, Callable[..., Criterion]]
) -> tuple[list[str | int], Any, Callable[..., Criterion]]:
    """
    Extracts the key parts, filter value and operator from a JSON filter dictionary.
    """
    ((key, filter_value),) = value.items()
    key_parts = [int(item) if item.isdigit() else str(item) for item in key.split("__")]
    operator_ = (
        operator_keywords[str(key_parts.pop(-1))]
        if key_parts[-1] in operator_keywords
        else operator.eq
    )
    return key_parts, filter_value, operator_


def resolve_field_json_path(field_term: Term, key_parts: list[str | int]) -> Term:
    """
    Resolves a JSON path from a list of key parts, e.g. converting
    (field, ['a', 'b', 'c']) to field->'a'->'b'->>'c'. Returns a pypika Term.
    """
    return JSONAttributeCriterion(field_term, key_parts)
