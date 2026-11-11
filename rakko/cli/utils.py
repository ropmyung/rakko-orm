# Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
# Derived from Tortoise ORM; maintained and modified for Rakko ORM.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import importlib
import importlib.util
import os
import sys
import tomllib
from collections.abc import Iterable
from pathlib import Path
from types import ModuleType
from typing import Any

from rakko.config import RakkoConfig
from rakko.exceptions import ConfigurationError


class CLIError(Exception):
    pass


class CLIUsageError(CLIError):
    pass


def rakko_orm_config(file: str = "pyproject.toml") -> str:
    """
    Get rakko orm config from env or pyproject.toml.

    :param file: toml file that contains tool.rakko settings
    :return: module path and var name that stores the rakko config
    """
    if not (config := os.getenv("RAKKO_ORM", "")) and (p := Path(file)).exists():
        doc = tomllib.loads(p.read_text("utf-8"))
        config = doc.get("tool", {}).get("rakko", {}).get("rakko_orm", "")
    return config


def get_rakko_config(config: str) -> RakkoConfig:
    """
    Get rakko config from module path with validation.

    :param config: module path + var name, e.g. "settings.RAKKO_ORM"
    :raises CLIUsageError: If config path is invalid (missing variable name)
    :raises CLIError: If module can't be imported, variable doesn't exist, or config is invalid
    :return: RakkoConfig instance (converts dict configs automatically)
    """
    if not config or not config.strip():
        raise CLIUsageError(
            "Config path cannot be empty.\n"
            "Expected format: module.VARIABLE (e.g., 'config.RAKKO_ORM')\n"
            "Or use --config-file to load from a file."
        )

    splits = config.split(".")
    if len(splits) < 2:
        raise CLIUsageError(
            f"Invalid config path format: '{config}'\n"
            f"Expected format: module.VARIABLE (e.g., 'config.RAKKO_ORM')\n"
            f"Got: '{config}' which has no variable name after the module.\n"
            f"Alternative: use --config-file to load from a JSON/YAML file."
        )

    config_path = ".".join(splits[:-1])
    rakko_config = splits[-1]

    if not config_path or not config_path.strip():
        raise CLIUsageError(
            f"Invalid config path: '{config}'\n"
            f"Module path is empty. Expected format: module.VARIABLE"
        )

    try:
        config_module = importlib.import_module(config_path)
    except ModuleNotFoundError:
        raise CLIError(
            f"Cannot import configuration module: '{config_path}'\n"
            f"Make sure the module exists and is in your Python path.\n"
            f"Current working directory: {Path.cwd()}\n"
            f"Python path: {sys.path[:3]}...\n"
            f"Hint: Try running from the directory containing '{config_path.split('.')[0]}'"
        ) from None
    except Exception as exc:
        raise CLIError(
            f"Error importing module '{config_path}': {type(exc).__name__}: {exc}"
        ) from None

    config_value = getattr(config_module, rakko_config, None)
    if config_value is None:
        available_vars = [
            name for name in dir(config_module) if not name.startswith("_") and name.isupper()
        ]
        hint = ""
        if available_vars:
            hint = f"\nAvailable config-like variables in {config_path}: {', '.join(available_vars[:5])}"

        raise CLIError(
            f"Variable '{rakko_config}' not found in module '{config_path}'\n"
            f"Checked: {config_module.__file__}{hint}\n"
            f"Make sure '{rakko_config}' is defined and not None."
        )

    if isinstance(config_value, RakkoConfig):
        return config_value

    if not isinstance(config_value, dict):
        raise CLIError(
            f"Config variable '{config}' must be a dict or RakkoConfig instance, got {type(config_value).__name__}\n"
            f"Expected structure (as dict): {{\n"
            f"    'connections': {{'default': 'sqlite://:memory:'}},\n"
            f"    'apps': {{'models': {{'models': ['app.models'], 'default_connection': 'default'}}}}\n"
            f"}}\n"
            f"Or import and use: from rakko.config import RakkoConfig, DBUrlConfig, AppConfig"
        )

    try:
        return RakkoConfig.from_dict(config_value)
    except ConfigurationError as exc:
        raise CLIError(
            f"Invalid Rakko ORM configuration in '{config}':\n"
            f"  {exc}\n\n"
            f"Expected structure:\n"
            f"  - 'connections': dict with at least one database connection\n"
            f"  - 'apps': dict with at least one app configuration\n\n"
            f"Example:\n"
            f"  RAKKO_ORM = {{\n"
            f"      'connections': {{'default': 'sqlite://:memory:'}},\n"
            f"      'apps': {{\n"
            f"          'models': {{\n"
            f"              'models': ['myapp.models'],\n"
            f"              'default_connection': 'default'\n"
            f"          }}\n"
            f"      }}\n"
            f"  }}"
        ) from None


def _first_models_module(models: Iterable[ModuleType | str] | str | None) -> str | None:
    if isinstance(models, str):
        return models
    if not models:
        return None
    for item in models:
        if isinstance(item, str):
            return item
        if isinstance(item, ModuleType):
            return item.__name__
    return None


def infer_migrations_module(models: Iterable[ModuleType | str] | str | None) -> str | None:
    module = _first_models_module(models)
    if not module:
        return None
    if module.endswith(".models"):
        base = module[: -len(".models")]
    elif "." in module:
        base = module.rsplit(".", 1)[0]
    else:
        base = module
    return f"{base}.migrations"


def normalize_apps_config(apps_config: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    normalized: dict[str, dict[str, Any]] = {}
    for label, config in apps_config.items():
        updated = dict(config)
        if "migrations" not in updated:
            inferred = infer_migrations_module(updated.get("models"))
            if inferred:
                try:
                    if importlib.util.find_spec(inferred) is not None:
                        updated["migrations"] = inferred
                except (ModuleNotFoundError, AttributeError, ValueError):
                    # Module doesn't exist or isn't a package - skip migrations inference
                    pass
        normalized[label] = updated
    return normalized
