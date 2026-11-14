import subprocess
import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("module", "expected"),
    [
        ("basic", "Remaining: 1"),
        ("queries", "Members per guild:"),
        ("relations", "Filtered prefetch: ['Alice']"),
        ("bulk_and_transactions", "Committed guild: Builders"),
        ("constraints", "Available stock: [{'sku': 'RAKKO-001', 'quantity': 10, 'reserved': 2}]"),
    ],
)
def test_sqlite_examples(module: str, expected: str) -> None:
    result = subprocess.run(
        [sys.executable, "-B", "-m", f"examples.{module}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert expected in result.stdout


@pytest.mark.asyncio
async def test_mysql_preview_does_not_open_connections(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from examples import mysql_sql
    from rakko.backends.mysql.client import MySQLClient

    create_connection = AsyncMock(side_effect=AssertionError("SQL preview must not connect"))
    monkeypatch.setattr(MySQLClient, "create_connection", create_connection)
    await mysql_sql.run()
    create_connection.assert_not_called()
    output = capsys.readouterr().out
    assert "BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT" in output
    assert "FROM `usage`" in output
    assert "UPDATE `usage`" in output
