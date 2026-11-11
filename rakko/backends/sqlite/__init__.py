# Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
# Derived from Tortoise ORM; maintained and modified for Rakko ORM.
# SPDX-License-Identifier: Apache-2.0

from .client import SqliteClient, SqliteClientWithRegexpSupport

client_class = SqliteClient


def get_client_class(db_info: dict):
    if db_info.get("credentials", {}).get("install_regexp_functions"):
        return SqliteClientWithRegexpSupport
    else:
        return SqliteClient
