# Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
# Derived from Tortoise ORM; maintained and modified for Rakko ORM.
# SPDX-License-Identifier: Apache-2.0

"""Shared models for the query, relation and bulk examples."""

from __future__ import annotations

from rakko import Field, Model, fields, reverse_relation


class Guild(Model):
    id: Field[int] = fields.BigAutoField(unsigned=True)
    name: Field[str] = fields.CharField(100, unique=True, source_field="guild_name")

    @reverse_relation
    def members(self) -> Member: ...


class Member(Model):
    id: Field[int] = fields.BigAutoField(unsigned=True)
    name: Field[str] = fields.CharField(100, unique=True, source_field="display_name")
    age: Field[int] = fields.IntField(default=0)
    note: Field[str | None] = fields.TextField(null=True)
    preferences: Field[dict[str, str] | None] = fields.JSONField[dict[str, str] | None](null=True)
    guild: Field[Guild] = fields.ForeignKeyField(Guild, related_name="members")
