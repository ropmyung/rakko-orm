# Modified for Rakko ORM: port package imports and internal references to the rakko namespace.

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from types import CoroutineType
from typing import TYPE_CHECKING, Any, cast

from rakko.connection import get_connections
from rakko.exceptions import ParamsError

if TYPE_CHECKING:  # pragma: nocoverage
    from rakko.backends.base.client import BaseDBAsyncClient, TransactionContext


def _get_connection(connection_name: str | None) -> BaseDBAsyncClient:
    conn_handler = get_connections()
    if connection_name:
        connection = conn_handler.get(connection_name)
    elif len(conn_handler.db_config) == 1:
        connection_name = next(iter(conn_handler.db_config.keys()))
        connection = conn_handler.get(connection_name)
    else:
        raise ParamsError(
            "You are running with multiple databases, so you should specify"
            f" connection_name: {list(conn_handler.db_config)}"
        )
    return connection


def in_transaction(connection_name: str | None = None) -> TransactionContext:
    """
    Transaction context manager.

    You can run your code inside ``async with in_transaction():`` statement to run it
    into one transaction. If error occurs transaction will rollback.

    :param connection_name: name of connection to run with, optional if you have only
                            one db connection
    """
    connection = _get_connection(connection_name)
    return connection._in_transaction()


def atomic[F: Callable[..., CoroutineType[Any, Any, Any]]](
    connection_name: str | None = None,
) -> Callable[[F], F]:
    """
    Transaction decorator.

    You can wrap your function with this decorator to run it into one transaction.
    If error occurs transaction will rollback.

    :param connection_name: name of connection to run with, optional if you have only
                            one db connection
    """

    def wrapper(func: F) -> F:
        @wraps(func)
        async def wrapped(*args, **kwargs) -> Any:
            async with in_transaction(connection_name):
                return await func(*args, **kwargs)

        return cast(F, wrapped)

    return wrapper
