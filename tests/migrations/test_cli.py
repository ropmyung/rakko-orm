import sqlite3
from pathlib import Path

import pytest

from tests.migrations.utils import cli, run_model_code


def test_generate_apply_and_rollback(project: Path) -> None:
    assert "Created" in cli(project, "makemigrations")
    migration = next((project / "sample/migrations").glob("0001_*.py"))
    source = migration.read_text(encoding="utf-8")
    assert "from tortoise" not in source
    compile(source, str(migration), "exec")
    cli(project, "migrate")
    with sqlite3.connect(project / "database.sqlite3") as connection:
        connection.execute("INSERT INTO accounts (balance) VALUES (10)")
        assert connection.execute("SELECT id FROM accounts").fetchone() == (1,)
        assert connection.execute("SELECT count(*) FROM rakko_migrations").fetchone() == (1,)
    assert "No changes" in cli(project, "makemigrations")
    cli(project, "downgrade", "sample")
    with sqlite3.connect(project / "database.sqlite3") as connection:
        assert connection.execute("SELECT count(*) FROM rakko_migrations").fetchone() == (0,)
        assert not connection.execute("SELECT name FROM sqlite_master WHERE name='accounts'").fetchall()


def test_check_constraint_round_trip(project: Path) -> None:
    models = project / "sample/models.py"
    models.write_text(
        "from rakko.migrations.constraints import CheckConstraint\n"
        + models.read_text(encoding="utf-8")
        + "        constraints = [CheckConstraint(\n"
        "            check=lambda: Account.balance >= 0, name='positive_balance')]\n",
        encoding="utf-8",
    )
    cli(project, "makemigrations")
    cli(project, "migrate")
    assert "No changes" in cli(project, "makemigrations")
    with sqlite3.connect(project / "database.sqlite3") as connection:
        connection.execute("INSERT INTO accounts (balance) VALUES (1)")
        with pytest.raises(sqlite3.IntegrityError, match="positive_balance"):
            connection.execute("INSERT INTO accounts (balance) VALUES (-1)")
    cli(project, "downgrade", "sample")


def test_schema_changes_preserve_data(project: Path) -> None:
    cli(project, "makemigrations")
    first = next((project / "sample/migrations").glob("0001_*.py")).stem
    cli(project, "migrate")
    with sqlite3.connect(project / "database.sqlite3") as connection:
        connection.execute("INSERT INTO accounts (balance) VALUES (42)")
    models = project / "sample/models.py"
    initial = models.read_text(encoding="utf-8")
    models.write_text(initial.replace(
        "    @meta", "    note: Field[str | None] = fields.TextField(null=True)\n    @meta"
    ), encoding="utf-8")
    cli(project, "makemigrations", "--name", "add_note")
    cli(project, "migrate")
    with sqlite3.connect(project / "database.sqlite3") as connection:
        assert connection.execute("SELECT balance, note FROM accounts").fetchone() == (42, None)
        connection.execute("UPDATE accounts SET note='kept'")
    models.write_text(models.read_text(encoding="utf-8").replace(
        "fields.IntField(default=0)", "fields.BigIntField(default=0)"
    ), encoding="utf-8")
    cli(project, "makemigrations", "--name", "big_balance")
    cli(project, "migrate")
    assert "No changes" in cli(project, "makemigrations")
    with sqlite3.connect(project / "database.sqlite3") as connection:
        assert connection.execute("SELECT balance, note FROM accounts").fetchone() == (42, "kept")
    cli(project, "downgrade", "sample", first)
    with sqlite3.connect(project / "database.sqlite3") as connection:
        assert connection.execute("SELECT balance FROM accounts").fetchone() == (42,)
        assert [row[1] for row in connection.execute("PRAGMA table_info(accounts)")] == ["id", "balance"]


def test_constraints_and_indexes_survive_alteration(project: Path) -> None:
    models = project / "sample/models.py"
    models.write_text(
        "from rakko.migrations.constraints import CheckConstraint, UniqueConstraint\n"
        "from rakko.indexes import Index\n"
        + models.read_text(encoding="utf-8").split("    @meta")[0]
        + "    Meta = MetaOption(table='accounts', constraints=[\n"
        "        CheckConstraint(lambda: Account.balance >= 0, 'positive'),\n"
        "        UniqueConstraint(fields=(balance,), name='balance_unique')],\n"
        "        indexes=[Index(fields=(balance,), name='balance_idx')])\n",
        encoding="utf-8",
    )
    cli(project, "makemigrations")
    cli(project, "migrate")
    with sqlite3.connect(project / "database.sqlite3") as connection:
        connection.execute("INSERT INTO accounts (balance) VALUES (3)")
    models.write_text(models.read_text(encoding="utf-8").replace(
        "fields.IntField(default=0)", "fields.BigIntField(default=0)"
    ), encoding="utf-8")
    cli(project, "makemigrations")
    cli(project, "migrate")
    assert "No changes" in cli(project, "makemigrations")
    with sqlite3.connect(project / "database.sqlite3") as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("INSERT INTO accounts (balance) VALUES (-1)")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("INSERT INTO accounts (balance) VALUES (3)")
        assert "balance_idx" in {row[1] for row in connection.execute("PRAGMA index_list(accounts)")}


def test_constraint_changes_and_rollback(project: Path) -> None:
    cli(project, "makemigrations")
    first = next((project / "sample/migrations").glob("0001_*.py")).stem
    cli(project, "migrate")
    models = project / "sample/models.py"
    models.write_text(
        "from rakko.migrations.constraints import CheckConstraint\n"
        + models.read_text(encoding="utf-8")
        + "        constraints = [CheckConstraint(lambda: Account.balance.between(0, 100), 'range')]\n",
        encoding="utf-8",
    )
    cli(project, "makemigrations")
    cli(project, "migrate")
    assert "No changes" in cli(project, "makemigrations")
    with sqlite3.connect(project / "database.sqlite3") as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("INSERT INTO accounts (balance) VALUES (101)")
    models.write_text(models.read_text(encoding="utf-8").replace("'range'", "'balance_range'"), encoding="utf-8")
    cli(project, "makemigrations")
    cli(project, "migrate")
    assert "No changes" in cli(project, "makemigrations")
    cli(project, "downgrade", "sample", first)
    with sqlite3.connect(project / "database.sqlite3") as connection:
        connection.execute("INSERT INTO accounts (balance) VALUES (101)")


def test_relation_and_nullable_field_snapshots(project: Path) -> None:
    models = project / "sample/models.py"
    models.write_text(models.read_text(encoding="utf-8") +
        "\nclass Entry(Model):\n"
        "    id: Field[int] = fields.BigAutoField(unsigned=True)\n"
        "    account: Field[Account] = fields.ForeignKeyField(Account, related_name='entries')\n"
        "    payload: Field[dict | None] = fields.JSONField(null=True)\n"
        "    text: Field[str | None] = fields.TextField(null=True)\n",
        encoding="utf-8")
    cli(project, "makemigrations")
    cli(project, "migrate")
    assert "No changes" in cli(project, "makemigrations")
    with sqlite3.connect(project / "database.sqlite3") as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("INSERT INTO accounts (balance) VALUES (1)")
        connection.execute("INSERT INTO entry (account_id) VALUES (1)")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("INSERT INTO entry (account_id) VALUES (999)")
    cli(project, "downgrade", "sample")


def test_sql_history_heads_and_dry_run(project: Path) -> None:
    cli(project, "init")
    cli(project, "makemigrations", "--name", "initial")
    assert "0001_initial" in cli(project, "heads")
    sql = cli(project, "sqlmigrate", "sample", "0001_initial")
    assert "accounts" in sql and "CREATE TABLE" in sql
    cli(project, "migrate", "--dry-run")
    with sqlite3.connect(project / "database.sqlite3") as connection:
        assert not connection.execute("SELECT name FROM sqlite_master WHERE name='accounts'").fetchall()
    cli(project, "migrate")
    assert "0001_initial" in cli(project, "history")
    assert "No changes" in cli(project, "makemigrations")


def test_parent_table_alteration_preserves_related_rows(project: Path) -> None:
    models = project / "sample/models.py"
    models.write_text(models.read_text(encoding="utf-8") +
        "\nclass Entry(Model):\n"
        "    id: Field[int] = fields.AutoField()\n"
        "    account: Field[Account] = fields.ForeignKeyField(Account, related_name='entries')\n",
        encoding="utf-8")
    cli(project, "makemigrations")
    cli(project, "migrate")
    with sqlite3.connect(project / "database.sqlite3") as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("INSERT INTO accounts (balance) VALUES (1)")
        connection.execute("INSERT INTO entry (account_id) VALUES (1)")
    models.write_text(models.read_text(encoding="utf-8").replace(
        "fields.IntField(default=0)", "fields.BigIntField(default=0)"
    ), encoding="utf-8")
    cli(project, "makemigrations")
    cli(project, "migrate")
    with sqlite3.connect(project / "database.sqlite3") as connection:
        assert connection.execute("SELECT account_id FROM entry").fetchall() == [(1,)]
        assert not connection.execute("PRAGMA foreign_key_check").fetchall()


def test_conditional_unique_constraint_survives_rebuild(project: Path) -> None:
    models = project / "sample/models.py"
    models.write_text(
        "from rakko.migrations.constraints import UniqueConstraint\n"
        + models.read_text(encoding="utf-8").split("    @meta")[0]
        + "    Meta = MetaOption(table='accounts', constraints=[\n"
        "        UniqueConstraint(fields=(balance,), condition=lambda: Account.balance > 0, name='unique_positive')])\n",
        encoding="utf-8")
    cli(project, "makemigrations")
    cli(project, "migrate")
    with sqlite3.connect(project / "database.sqlite3") as connection:
        connection.executemany("INSERT INTO accounts (balance) VALUES (?)", [(0,), (0,), (1,)])
    models.write_text(models.read_text(encoding="utf-8").replace(
        "fields.IntField(default=0)", "fields.BigIntField(default=0)"
    ), encoding="utf-8")
    cli(project, "makemigrations")
    cli(project, "migrate")
    assert "No changes" in cli(project, "makemigrations")
    with sqlite3.connect(project / "database.sqlite3") as connection:
        connection.execute("INSERT INTO accounts (balance) VALUES (0)")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("INSERT INTO accounts (balance) VALUES (1)")


def test_fake_apply_and_unapply(project: Path) -> None:
    cli(project, "makemigrations")
    cli(project, "migrate", "--fake")
    with sqlite3.connect(project / "database.sqlite3") as connection:
        assert connection.execute("SELECT count(*) FROM rakko_migrations").fetchone() == (1,)
        assert not connection.execute("SELECT name FROM sqlite_master WHERE name='accounts'").fetchall()
    cli(project, "downgrade", "sample", "--fake")
    cli(project, "upgrade", "sample")
    with sqlite3.connect(project / "database.sqlite3") as connection:
        connection.execute("INSERT INTO accounts (balance) VALUES (1)")


def test_failed_migration_is_atomic(project: Path) -> None:
    cli(project, "makemigrations")
    migration = next((project / "sample/migrations").glob("0001_*.py"))
    migration.write_text(migration.read_text(encoding="utf-8") +
        "\nMigration.operations.append(ops.RunSQL('INVALID SQL'))\n", encoding="utf-8")
    with pytest.raises(AssertionError, match="syntax error"):
        cli(project, "migrate")
    with sqlite3.connect(project / "database.sqlite3") as connection:
        assert connection.execute("SELECT count(*) FROM rakko_migrations").fetchone() == (0,)
        assert not connection.execute("SELECT name FROM sqlite_master WHERE name='accounts'").fetchall()


def test_migration_record_failure_rolls_back_schema(project: Path) -> None:
    cli(project, "makemigrations")
    migration = next((project / "sample/migrations").glob("0001_*.py"))
    migration.write_text(migration.read_text(encoding="utf-8") +
        "\nMigration.operations.append(ops.RunSQL('DROP TABLE rakko_migrations'))\n", encoding="utf-8")
    with pytest.raises(AssertionError, match="no such table"):
        cli(project, "migrate")
    with sqlite3.connect(project / "database.sqlite3") as connection:
        assert connection.execute("SELECT count(*) FROM rakko_migrations").fetchone() == (0,)
        assert not connection.execute("SELECT name FROM sqlite_master WHERE name='accounts'").fetchall()


def test_many_to_many_snapshot_and_execution(project: Path) -> None:
    models = project / "sample/models.py"
    models.write_text(models.read_text(encoding="utf-8") +
        "\nclass Collection(Model):\n"
        "    id: Field[int] = fields.AutoField()\n"
        "    accounts = fields.ManyToManyField(Account, related_name='collections')\n",
        encoding="utf-8")
    cli(project, "makemigrations")
    cli(project, "migrate")
    assert "No changes" in cli(project, "makemigrations")
    run_model_code(project,
        "from sample.models import Collection\n"
        "account = await Account.create(balance=1)\n"
        "collection = await Collection.create()\n"
        "await collection.accounts.add(account)\n"
        "assert await collection.accounts.all().count() == 1"
    )
    cli(project, "downgrade", "sample")


def test_schema_generation_enforces_constraint_expressions(project: Path) -> None:
    models = project / "sample/models.py"
    models.write_text(
        "from rakko.migrations.constraints import CheckConstraint, UniqueConstraint\n"
        "from rakko.indexes import Index\n"
        + models.read_text(encoding="utf-8").split("    @meta")[0].replace(
            "fields.IntField(default=0)", "fields.IntField(default=0, source_field='stored_balance')"
        )
        + "    Meta = MetaOption(table='accounts', constraints=[\n"
        "        CheckConstraint(lambda: Account.balance >= 0, 'positive'),\n"
        "        UniqueConstraint(fields=(balance,), name='unique_positive', condition=lambda: Account.balance > 0)],\n"
        "        indexes=[Index(fields=(balance,), name='balance_idx')])\n",
        encoding="utf-8")
    run_model_code(project,
        "await context.generate_schemas()\n"
        "from rakko.connection import get_connection\n"
        "_, columns = await get_connection('default').execute_query('PRAGMA index_info(balance_idx)')\n"
        "assert columns[0]['name'] == 'stored_balance'\n"
        "await Account.create(balance=0)\n"
        "await Account.create(balance=0)\n"
        "await Account.create(balance=1)\n"
        "for balance in [-1, 1]:\n"
        "    try:\n"
        "        await Account.create(balance=balance)\n"
        "    except IntegrityError:\n"
        "        pass\n"
        "    else:\n"
        "        raise AssertionError('Constraint not enforced')"
    )


@pytest.mark.parametrize("column", ["balance", "stored_balance"])
def test_source_column_round_trip_and_rename(project: Path, column: str) -> None:
    models = project / "sample/models.py"
    models.write_text(models.read_text(encoding="utf-8").replace(
        "fields.IntField(default=0)", f'fields.IntField(default=0, source_field="{column}")'
    ), encoding="utf-8")
    cli(project, "makemigrations")
    cli(project, "migrate")
    first = next((project / "sample/migrations").glob("0001_*.py")).stem
    run_model_code(project, "await Account.create(balance=5)")
    models.write_text(models.read_text(encoding="utf-8").replace(
        f'source_field="{column}"', 'source_field="renamed_balance"'
    ), encoding="utf-8")
    cli(project, "makemigrations")
    cli(project, "migrate")
    run_model_code(project, "assert (await Account.get(Account.balance == 5)).balance == 5")
    assert "No changes" in cli(project, "makemigrations")
    cli(project, "downgrade", "sample", first)
    with sqlite3.connect(project / "database.sqlite3") as connection:
        assert connection.execute(f'SELECT "{column}" FROM accounts').fetchall() == [(5,)]


def test_renamed_field_and_model_keep_data(project: Path) -> None:
    cli(project, "makemigrations")
    first = next((project / "sample/migrations").glob("0001_*.py")).stem
    cli(project, "migrate")
    models = project / "sample/models.py"
    run_model_code(project, "await Account.create(balance=7)")
    models.write_text(models.read_text(encoding="utf-8").replace("balance", "credit"), encoding="utf-8")
    cli(project, "makemigrations")
    cli(project, "migrate")
    assert "No changes" in cli(project, "makemigrations")
    with sqlite3.connect(project / "database.sqlite3") as connection:
        assert connection.execute("SELECT credit FROM accounts").fetchall() == [(7,)]
    models.write_text(models.read_text(encoding="utf-8").replace("class Account", "class Wallet"), encoding="utf-8")
    cli(project, "makemigrations")
    cli(project, "migrate")
    assert "No changes" in cli(project, "makemigrations")
    cli(project, "downgrade", "sample", first)
    with sqlite3.connect(project / "database.sqlite3") as connection:
        assert connection.execute("SELECT balance FROM accounts").fetchall() == [(7,)]
