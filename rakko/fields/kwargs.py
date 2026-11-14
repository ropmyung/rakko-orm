from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, TypedDict

from rakko.fields.base import _DB_DEFAULT_NOT_SET
from rakko.fields.db_defaults import SqlDefault
from rakko.validators import Validator

if TYPE_CHECKING:
    from rakko.models import Model


class _FieldKwargsCommon[T](TypedDict, total=False):
    """:class:`Field` constructor arguments that are never declared as explicit parameters.

    Used with :data:`typing.Unpack` to give ``**kwargs`` explicit type hints. This is the
    smallest set; fields that declare ``unique``/``db_index``/``primary_key`` explicitly
    (e.g. ``TextField``) unpack this directly to avoid PEP 692 parameter-name collisions.
    """

    source_field: str | None
    default: T | Callable[..., T | Awaitable[T]] | None
    db_default: T | SqlDefault | _DB_DEFAULT_NOT_SET
    description: str | None
    model: "Model | None"
    validators: list[Validator | Callable]
    pk: bool  # deprecated alias for primary_key
    index: bool  # deprecated alias for db_index


class FieldKwargsNoPk[T](_FieldKwargsCommon[T], total=False):
    """Common arguments excluding ``primary_key`` and ``null``.

    For constructors that declare ``primary_key`` and ``null`` as explicit parameters
    (e.g. ``IntField``).
    """

    unique: bool
    db_index: bool | None


class FieldKwargs[T](FieldKwargsNoPk[T], total=False):
    """Common arguments excluding ``null``.

    For constructors that declare only ``null`` as an explicit parameter (the majority).
    """

    primary_key: bool | None


class RelationalFieldKwargs[T](FieldKwargs[T], total=False):
    """Constructor arguments for :func:`ForeignKeyField` and :func:`OneToOneField`.

    Extends the common :class:`~tortoise.fields.base.FieldKwargs` with ``to_field``.
    ``null`` is declared as an explicit parameter on those constructors, so it is omitted.
    """

    to_field: str | None


class ManyToManyFieldKwargs[T](_FieldKwargsCommon[T], total=False):
    """Constructor arguments for :func:`ManyToManyField`.

    ``unique`` is declared as an explicit parameter, so it is omitted here; the deprecated
    ``create_unique_index`` alias is still accepted.
    """

    create_unique_index: bool  # deprecated alias for unique
