import os
from pathlib import Path
from uuid import uuid4

import pytest

from tests.migrations.utils import cli, run_model_code


@pytest.mark.parametrize("driver", ["aiomysql", "asyncmy", "asyncpg", "psycopg"])
def test_live_database_migration_cycle(
    project: Path, driver: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    variable = (
        "RAKKO_MIGRATION_MYSQL_URL"
        if driver in {"aiomysql", "asyncmy"}
        else "RAKKO_MIGRATION_POSTGRES_URL"
    )
    url = os.getenv(variable)
    if not url:
        pytest.skip(f"Set {variable} to a disposable test database")
    if driver in {"aiomysql", "asyncmy"}:
        monkeypatch.setenv("RAKKO_TEST_MYSQL_DRIVER", driver)
    else:
        url = url.replace("asyncpg://", f"{driver}://", 1)
    app = f"app_{uuid4().hex[:10]}"
    settings = project / "settings.py"
    settings.write_text(
        settings.read_text(encoding="utf-8")
        .replace("'sqlite://database.sqlite3'", repr(url))
        .replace("'sample':", f"'{app}':"),
        encoding="utf-8",
    )
    models = project / "sample/models.py"
    unique_condition = (
        ", condition=lambda model: model.balance > 0" if driver in {"asyncpg", "psycopg"} else ""
    )
    models.write_text(
        "from rakko.migrations.constraints import CheckConstraint, UniqueConstraint\n"
        + models.read_text(encoding="utf-8").split("    @meta")[0]
        + f"    Meta = MetaOption(table='accounts_{app}', constraints=[\n"
        + f"        CheckConstraint(lambda model: model.balance >= 0, 'check_{app}'),\n"
        + f"        UniqueConstraint(fields=(balance,), name='unique_{app}'{unique_condition})])\n"
        + "\nclass Marker(Model):\n    id: Field[int] = fields.AutoField()\n"
        + f"    Meta = MetaOption(table='marker_{app}')\n",
        encoding="utf-8",
    )
    cli(project, "makemigrations", "--name", "initial")
    assert "CREATE TABLE" in cli(project, "sqlmigrate", app, "0001_initial")
    cli(project, "migrate")
    run_model_code(
        project,
        "from sample.models import Marker\n"
        "marker = await Marker.create()\n"
        "assert marker.id == 1 and await Marker.all().count() == 1\n"
        "account = await Account.create(balance=42)\n"
        "assert account.id == 1\n"
        "try:\n"
        "    await Account.create(balance=-1)\n"
        "except IntegrityError:\n"
        "    pass\n"
        "else:\n"
        "    raise AssertionError('CHECK was not enforced')\n"
        "try:\n"
        "    await Account.create(balance=42)\n"
        "except IntegrityError:\n"
        "    pass\n"
        "else:\n"
        "    raise AssertionError('UNIQUE was not enforced')",
    )
    models.write_text(
        models.read_text(encoding="utf-8")
        .replace("fields.IntField(default=0)", "fields.BigIntField(default=0)")
        .replace(
            "    Meta =", "    note: Field[str | None] = fields.TextField(null=True)\n    Meta ="
        ),
        encoding="utf-8",
    )
    cli(project, "makemigrations", "--name", "alter_balance")
    cli(project, "migrate")
    assert "No changes" in cli(project, "makemigrations")
    run_model_code(
        project,
        "account = await Account.get(Account.balance == 42)\n"
        "assert account.note is None\n"
        "from rakko.transactions import in_transaction\n"
        "async with in_transaction():\n"
        "    await Account.filter(Account.id == account.id).update(note='kept')\n"
        "    try:\n"
        "        async with in_transaction():\n"
        "            await Account.filter(Account.id == account.id).update(balance=-1)\n"
        "    except IntegrityError:\n"
        "        pass\n"
        "    else:\n"
        "        raise AssertionError('Nested constraint violation was accepted')\n"
        "    async with in_transaction():\n"
        "        assert (await Account.get(Account.id == account.id)).balance == 42",
    )
    cli(project, "downgrade", app, "0001_initial")
    cli(project, "upgrade", app)
    run_model_code(
        project,
        "assert await Account.all().count() == 1\n"
        "account = await Account.get(Account.balance == 42)\n"
        "assert account.note is None",
    )
    assert "0002_alter_balance" in cli(project, "history")
    cli(project, "downgrade", app)
