# Copyright (c) 2026 ropmyung (Rakko ORM additions).
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

import pytest


@pytest.fixture
def project(tmp_path: Path) -> Path:
    package = tmp_path / "sample"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "models.py").write_text(
        "from rakko import Field, Model, fields\nfrom rakko.models import meta, MetaOption\n"
        "class Account(Model):\n"
        "    id: Field[int] = fields.AutoField()\n"
        "    balance: Field[int] = fields.IntField(default=0)\n"
        "    @meta\n"
        "    class Meta(MetaOption):\n"
        "        table = 'accounts'\n",
        encoding="utf-8",
    )
    (tmp_path / "settings.py").write_text(
        "RAKKO_ORM = {\n"
        "    'connections': {'default': 'sqlite://database.sqlite3'},\n"
        "    'apps': {'sample': {'models': ['sample.models'],\n"
        "                        'migrations': 'sample.migrations'}},\n"
        "}\n",
        encoding="utf-8",
    )
    return tmp_path

