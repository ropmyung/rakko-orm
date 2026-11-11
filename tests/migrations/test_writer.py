# Copyright (c) 2026 ropmyung (Rakko ORM additions).
# SPDX-License-Identifier: Apache-2.0

import importlib

import pytest
from pypika_tortoise.context import DEFAULT_SQL_CONTEXT
from pypika_tortoise.functions import Cast, Length
from pypika_tortoise.terms import Field as SQLField
from pypika_tortoise.terms import Function

from rakko import fields
from rakko.migrations.constraints import CheckConstraint, UniqueConstraint
from rakko.migrations.writer import ImportManager, render_value


@pytest.mark.parametrize("factory", [
    fields.IntField, fields.SmallIntField, fields.BigIntField, fields.TinyIntField,
    fields.AutoField, fields.SmallAutoField, fields.BigAutoField, fields.TinyAutoField,
])
@pytest.mark.parametrize("unsigned", [False, True])
@pytest.mark.parametrize("primary_key", [False, True])
def test_integer_field_round_trip(factory, unsigned: bool, primary_key: bool) -> None:
    original = factory(unsigned=unsigned, primary_key=primary_key)
    path, args, kwargs = original.deconstruct()
    module, name = path.rsplit('.', 1)
    restored = getattr(importlib.import_module(module), name)(*args, **kwargs)
    assert type(restored) is type(original)
    assert restored.generated is original.generated
    assert restored.pk is original.pk
    assert restored.unsigned is original.unsigned
    for dialect in ["mysql", "postgres", "sqlite"]:
        assert restored.get_for_dialect(dialect, "SQL_TYPE") == original.get_for_dialect(dialect, "SQL_TYPE")
        if original.generated:
            assert restored.get_for_dialect(dialect, "GENERATED_SQL") == original.get_for_dialect(dialect, "GENERATED_SQL")


@pytest.mark.parametrize("expression", [
    SQLField("amount") >= 0,
    (SQLField("amount") >= 0) & (SQLField("amount") <= 10),
    (SQLField("amount") + 1) != 2,
    SQLField("amount").between(0, 10),
    SQLField("amount").isin([0, 1]),
    SQLField("amount").notin([0, 1]),
    SQLField("amount").isnull(),
    SQLField("amount").notnull(),
    ~(SQLField("amount") == 1),
    Function("ABS", SQLField("amount")) < 10,
    Length(SQLField("name")) > 0,
    SQLField("name") == "O'Reilly; value",
])
def test_expression_serialization_is_portable(expression) -> None:
    imports = ImportManager()
    code = render_value(expression, imports)
    namespace = {}
    exec("\n".join(imports.render()), namespace)
    restored = eval(code, namespace)
    for quote in ['"', '`']:
        context = DEFAULT_SQL_CONTEXT.copy(quote_char=quote)
        assert restored.get_sql(context) == expression.get_sql(context)


@pytest.mark.parametrize("constraint", [CheckConstraint, UniqueConstraint])
def test_constraint_rejects_string_conditions(constraint) -> None:
    with pytest.raises(TypeError, match="Criterion"):
        if constraint is CheckConstraint:
            constraint(check="amount > 0", name="positive")
        else:
            constraint(fields=("amount",), condition="amount > 0")


def test_special_function_is_not_silently_changed() -> None:
    with pytest.raises(ValueError, match="Cannot serialize SQL function Cast"):
        render_value(Cast(SQLField("amount"), "TEXT"), ImportManager())
