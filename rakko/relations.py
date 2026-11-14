# Added for Rakko ORM: provide explicit reverse-relation descriptors.

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, cast, get_type_hints, overload

from rakko.exceptions import ConfigurationError
from rakko.fields.relational import BackwardFKRelation, ForeignKeyFieldInstance, ReverseRelation

if TYPE_CHECKING:
    from rakko.fields.base import Field
    from rakko.models import Model


class RelationProperty(property):
    """Expose the relation field on classes and the related value on instances."""

    def __init__(self, field: Field, *args: Any) -> None:
        super().__init__(*args)
        self.field = field

    def __get__(self, instance: Any, owner: type | None = None) -> Any:
        if instance is None:
            from rakko.expressions import Query

            return Query(self.field)
        return super().__get__(instance, owner)


class reverse_relation[T: Model]:
    """Declare a reverse FK accessor using a function's related-model annotation."""

    def __init__(self, function: Callable[[Any], T]) -> None:
        self.function = function
        self.name = function.__name__

    def __set__(self, instance: Model, value: Any) -> None:
        raise AttributeError(f"Reverse relation {self.name!r} is read-only")

    @overload
    def __get__(self, instance: None, owner: type | None = None) -> reverse_relation[T]: ...

    @overload
    def __get__(self, instance: Model, owner: type | None = None) -> ReverseRelation[T]: ...

    def __get__(
        self, instance: Model | None, owner: type | None = None
    ) -> reverse_relation[T] | ReverseRelation[T]:
        if instance is None:
            return self
        owner = cast(type, type(instance))
        cache_name = f"_{self.name}"
        relation = instance.__dict__.get(cache_name)
        if relation is not None:
            return relation
        field = instance._meta.fields_map.get(self.name)
        if isinstance(field, BackwardFKRelation):
            relation = ReverseRelation(
                field.related_model,
                field.relation_field,
                instance,
                field.to_field_instance.model_field_name,
            )
        else:
            related_model = get_type_hints(self.function, localns={owner.__name__: owner})["return"]
            candidates = [
                fk
                for fk in related_model._meta.fields_map.values()
                if isinstance(fk, ForeignKeyFieldInstance) and fk.related_model is owner
            ]
            if len(candidates) != 1:
                raise ConfigurationError(
                    f"Cannot unambiguously resolve reverse relation {owner.__name__}.{self.name}"
                )
            fk = candidates[0]
            relation = ReverseRelation(
                related_model,
                cast(str, fk.source_field),
                instance,
                fk.to_field_instance.model_field_name,
            )
        setattr(instance, cache_name, relation)
        return relation
