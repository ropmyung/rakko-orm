# Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
# Derived from Tortoise ORM; maintained and modified for Rakko ORM.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import abc
import asyncio
from asyncio.events import AbstractEventLoop
from collections.abc import Awaitable, Callable
from functools import wraps
from types import CoroutineType
from typing import TYPE_CHECKING, Any, SupportsInt

from pypika_tortoise import PostgreSQLQuery, Query

from rakko.backends.base.client import (
    BaseDBAsyncClient,
    Capabilities,
    ConnectionWrapper,
    PasswordType,
    PoolConnectionWrapper,
    TransactionContext,
)
from rakko.backends.base.executor import BaseExecutor
from rakko.backends.base.schema_generator import BaseSchemaGenerator
from rakko.backends.base_postgres.executor import BasePostgresExecutor
from rakko.backends.base_postgres.schema_generator import BasePostgresSchemaGenerator

if TYPE_CHECKING:
    from asyncpg.connection import Connection
    from psycopg import AsyncConnection

type FuncType[**P, R] = Callable[P, CoroutineType[Any, Any, R]]


def translate_exceptions[**P, R](func: FuncType[P, R]) -> FuncType[P, R]:
    @wraps(func)
    async def _translate_exceptions(*args: P.args, **kwargs: P.kwargs) -> R:
        client = args[0]
        if not isinstance(client, BasePostgresClient):
            raise TypeError("Exception translation requires a PostgreSQL client")
        return await client._translate_exceptions(func, *args[1:], **kwargs)

    return _translate_exceptions


class BasePostgresPool:
    pass


class BasePostgresClient(BaseDBAsyncClient, abc.ABC):
    DSN_TEMPLATE = "postgres://{user}:{password}@{host}:{port}/{database}"
    query_class: type[Query] = PostgreSQLQuery
    executor_class: type[BaseExecutor] = BasePostgresExecutor
    schema_generator: type[BaseSchemaGenerator] = BasePostgresSchemaGenerator
    capabilities = Capabilities(
        "postgres",
        support_update_limit_order_by=False,
        support_for_posix_regex_queries=True,
        support_for_no_key_update=True,
        support_json_attributes=True,
        can_rollback_ddl=True,
        support_returning=True,
    )
    connection_class: type[AsyncConnection] | type[Connection] | None = None
    loop: AbstractEventLoop | None = None
    _pool: Any | None = None
    _connection: Any | None = None

    def __init__(
        self,
        user: str | None = None,
        password: PasswordType = None,
        database: str | None = None,
        host: str | None = None,
        port: SupportsInt = 5432,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)

        self.user = user
        self.password = password
        self.database = database
        self.host = host
        self.port = int(port)  # make sure port is int type
        self.extra = kwargs.copy()
        # we can't deep copy kwargs because of ssl context
        # since server_settings is a dict, we copy it again
        self.server_settings = (self.extra.pop("server_settings", None) or {}).copy()
        self.schema = self.extra.pop("schema", None)
        self.application_name = self.extra.pop("application_name", None)
        self.extra.pop("connection_name", None)
        self.extra.pop("fetch_inserted", None)
        self.loop = self.extra.pop("loop", None)
        self.connection_class = self.extra.pop("connection_class", self.connection_class)
        self.pool_minsize = int(self.extra.pop("minsize", 1))
        self.pool_maxsize = int(self.extra.pop("maxsize", 5))

        self._template: dict = {}
        self._pool = None
        self._connection = None
        self._pool_init_lock = asyncio.Lock()

    @abc.abstractmethod
    async def create_connection(self, with_db: bool) -> None:
        raise NotImplementedError("create_connection is not implemented")

    @abc.abstractmethod
    async def create_pool(self, **kwargs):
        raise NotImplementedError("create_pool is not implemented")

    @abc.abstractmethod
    async def _expire_connections(self) -> None:
        raise NotImplementedError("_expire_connections is not implemented")

    @abc.abstractmethod
    async def _close(self) -> None:
        raise NotImplementedError("_close is not implemented")

    @abc.abstractmethod
    async def _translate_exceptions[R](
        self, func: Callable[..., Awaitable[R]], *args: Any, **kwargs: Any
    ) -> R:
        raise NotImplementedError("translate_exceptions is not implemented")

    async def close(self) -> None:
        await self._close()
        self._template.clear()

    async def db_create(self) -> None:
        await self.create_connection(with_db=False)
        await self.execute_script(f'CREATE DATABASE "{self.database}" OWNER "{self.user}"')
        await self.close()

    async def db_delete(self) -> None:
        await self.create_connection(with_db=False)
        try:
            await self.execute_script(f'DROP DATABASE "{self.database}"')
        finally:
            await self.close()

    def acquire_connection(self) -> ConnectionWrapper | PoolConnectionWrapper:
        return PoolConnectionWrapper(self, self._pool_init_lock)

    @abc.abstractmethod
    def _in_transaction(self) -> TransactionContext:
        raise NotImplementedError("_in_transaction is not implemented")

    @abc.abstractmethod
    async def execute_insert(self, query: str, values: list) -> Any | None:
        raise NotImplementedError("execute_insert is not implemented")

    @abc.abstractmethod
    async def execute_many(self, query: str, values: list) -> None:
        raise NotImplementedError("execute_many is not implemented")

    @abc.abstractmethod
    async def execute_query(self, query: str, values: list | None = None) -> tuple[int, list[dict]]:
        raise NotImplementedError("execute_query is not implemented")

    @abc.abstractmethod
    async def execute_query_dict(self, query: str, values: list | None = None) -> list[dict]:
        raise NotImplementedError("execute_query_dict is not implemented")

    @translate_exceptions
    async def execute_script(self, query: str) -> None:
        async with self.acquire_connection() as connection:
            self.log.debug(query)
            await connection.execute(query)
