# Modified for Rakko ORM: integrate this module into the rakko package namespace.

from .client import SqliteClient, SqliteClientWithRegexpSupport

client_class = SqliteClient


def get_client_class(db_info: dict):
    if db_info.get("credentials", {}).get("install_regexp_functions"):
        return SqliteClientWithRegexpSupport
    else:
        return SqliteClient
