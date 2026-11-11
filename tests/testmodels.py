# Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
# Derived from Tortoise ORM; maintained and modified for Rakko ORM.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

from rakko import Field, Model, fields, reverse_relation


class Guild(Model):
    id: Field[int] = fields.AutoField()
    name: Field[str] = fields.CharField(100, unique=True, source_field="guild_name")

    @reverse_relation
    def members(self) -> Member: ...


class Member(Model):
    id: Field[int] = fields.AutoField()
    name: Field[str] = fields.CharField(100, unique=True, source_field="display_name")
    age: Field[int] = fields.IntField(default=0)
    note: Field[str | None] = fields.TextField(null=True)
    data: Field[dict[str, Any] | None] = fields.JSONField[dict[str, Any] | None](null=True)
    guild: Field[Guild] = fields.ForeignKeyField(Guild, related_name="members")


class Unrelated(Model):
    id: Field[int] = fields.AutoField()
    name: Field[str] = fields.CharField(100)


class DualGuild(Model):
    id: Field[int] = fields.AutoField()
    source: Field[Guild] = fields.ForeignKeyField(Guild, related_name=False)
    destination: Field[Guild] = fields.ForeignKeyField(Guild, related_name=False)


class PositionalRecord(Model):
    id: Field[int] = fields.AutoField()
    name: Field[str] = fields.CharField(100, unique=True)
    age: Field[int] = fields.IntField(default=0)

    def __init__(self, name: str, /, *, age: int = 0, **kwargs: Any) -> None:
        super().__init__(name=name, age=age, **kwargs)
