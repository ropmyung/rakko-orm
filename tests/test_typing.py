import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_pyright(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pyright",
            "--pythonpath",
            sys.executable,
            "--outputjson",
            str(path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        check=False,
    )


def test_constructor_and_query_types() -> None:
    result = run_pyright(ROOT / "tests" / "typing_queries.py")
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["summary"]["warningCount"] == 0


def test_invalid_query_arguments_are_rejected(tmp_path: Path) -> None:
    invalid_calls = [
        'Member.create(age="old")',
        'Member.all().update(age="old")',
        "Member.create(id=1)",
        "Member.filter(Guild.id == 1)",
        "Member.filter(Member.name == 1)",
        "Member.create(unknown=1)",
        "_ = cast(Field[int], fields.IntField()) + 1",
        "Member.get_or_create(Member.name == 'Alice', age=1.5)",
        "Member.update_or_create(Member.name == 'Alice', age=1.5)",
        "Member.get_or_create(Guild.name == 'Guild', name='Alice')",
        "Member.update_or_create(Guild.name == 'Guild', name='Alice')",
        "Member.get_or_create(Member.name == 'Alice', unknown=1)",
        "Member.update_or_create(Member.name == 'Alice', unknown=1)",
        "Member.get_or_create(Member.name == 'Alice', id=1)",
        "Member.update_or_create(Member.name == 'Alice', id=1)",
        "Member.get_or_create(Member.name == 'Alice', note=1)",
        "Member.update_or_create(Member.name == 'Alice', guild=1)",
        "CheckConstraint(check='age >= 0', name='positive')",
        "CheckConstraint(check=True, name='positive')",
        "UniqueConstraint(fields=(Member.age,), condition='age > 0')",
        "CheckConstraint[Member](check=lambda model: model.age == 'old', name='positive')",
        "CheckConstraint(check=lambda: Member.age >= 0, name='positive')",
        "Index(fields=(1,))",
    ]
    path = tmp_path / "invalid_queries.py"
    imports = [
        "from typing import cast",
        "from rakko import Field, fields",
        "from tests.testmodels import Guild, Member",
        "from rakko.migrations.constraints import CheckConstraint, UniqueConstraint",
        "from rakko.indexes import Index",
    ]
    path.write_text("\n".join([*imports, *invalid_calls]) + "\n", encoding="utf-8")
    result = run_pyright(path)
    assert result.returncode == 1, result.stdout + result.stderr
    diagnostics = json.loads(result.stdout)["generalDiagnostics"]
    error_lines = {
        diagnostic["range"]["start"]["line"]
        for diagnostic in diagnostics
        if diagnostic["severity"] == "error"
    }
    assert error_lines == set(range(len(imports), len(imports) + len(invalid_calls))), result.stdout
