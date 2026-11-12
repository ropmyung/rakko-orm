# Modified for Rakko ORM: test RAKKO_ORM and tool.rakko configuration lookup.

import importlib
from pathlib import Path
from types import ModuleType

import pytest

from rakko.cli import utils
from rakko.config import RakkoConfig

EMPTY_RAKKO_ORM = None


def test_rakko_orm_config_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAKKO_ORM", "app.settings.RAKKO_ORM")
    assert utils.rakko_orm_config() == "app.settings.RAKKO_ORM"


def test_rakko_orm_config_pyproject(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[tool.rakko]
rakko_orm = "settings.RAKKO_ORM"
""".lstrip(),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("RAKKO_ORM", raising=False)
    assert utils.rakko_orm_config() == "settings.RAKKO_ORM"


def test_rakko_orm_config_empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("RAKKO_ORM", raising=False)
    assert utils.rakko_orm_config() == ""


def test_get_rakko_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module_name = f"cli_settings_{tmp_path.name}"
    settings = tmp_path / f"{module_name}.py"
    settings.write_text(
        "RAKKO_ORM = {\n"
        "    'connections': {'default': 'sqlite://:memory:'},\n"
        "    'apps': {'models': {'models': ['__main__'], 'default_connection': 'default'}}\n"
        "}\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()
    import sys

    sys.modules.pop("cli_app", None)
    sys.modules.pop("cli_app.migrations", None)

    result = utils.get_rakko_config(f"{module_name}.RAKKO_ORM")
    assert isinstance(result, RakkoConfig)
    config_dict = result.to_dict()
    assert config_dict["connections"] == {"default": "sqlite://:memory:"}
    assert config_dict["apps"]["models"]["models"] == ["__main__"]

    with pytest.raises(
        utils.CLIError,
        match="Cannot import configuration module: 'missing'",
    ):
        utils.get_rakko_config("missing.RAKKO_ORM")

    with pytest.raises(
        utils.CLIError,
        match="Variable 'MISSING' not found in module",
    ):
        utils.get_rakko_config(f"{module_name}.MISSING")


def test_infer_migrations_module() -> None:
    module = ModuleType("demo.models")
    assert utils.infer_migrations_module([module]) == "demo.migrations"
    assert utils.infer_migrations_module(["demo.models"]) == "demo.migrations"
    assert utils.infer_migrations_module(["demo.sub.models"]) == "demo.sub.migrations"
    assert utils.infer_migrations_module(["demo.other"]) == "demo.migrations"
    assert utils.infer_migrations_module(None) is None


def test_normalize_apps_config_infers_migrations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app_dir = tmp_path / "cli_app"
    app_dir.mkdir()
    (app_dir / "__init__.py").write_text("", encoding="utf-8")
    (app_dir / "models.py").write_text("", encoding="utf-8")
    migrations_dir = app_dir / "migrations"
    migrations_dir.mkdir()
    (migrations_dir / "__init__.py").write_text("", encoding="utf-8")

    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()
    import sys

    sys.modules.pop("cli_app_no_migrations", None)
    sys.modules.pop("cli_app_no_migrations.migrations", None)
    apps = {
        "app": {
            "models": ["cli_app.models"],
            "default_connection": "default",
        }
    }
    normalized = utils.normalize_apps_config(apps)
    assert normalized["app"]["migrations"] == "cli_app.migrations"


def test_normalize_apps_config_skips_missing_module(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app_dir = tmp_path / "cli_app_no_migrations"
    app_dir.mkdir()
    (app_dir / "__init__.py").write_text("", encoding="utf-8")
    (app_dir / "models.py").write_text("", encoding="utf-8")

    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()
    apps = {
        "app": {
            "models": ["cli_app_no_migrations.models"],
            "default_connection": "default",
        }
    }
    normalized = utils.normalize_apps_config(apps)
    assert "migrations" not in normalized["app"]
