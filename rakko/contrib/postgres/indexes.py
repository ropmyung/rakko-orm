# Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
# Derived from Tortoise ORM; maintained and modified for Rakko ORM.
# SPDX-License-Identifier: Apache-2.0

from rakko.indexes import PartialIndex


class PostgreSQLIndex(PartialIndex):
    pass


class BloomIndex(PostgreSQLIndex):
    INDEX_TYPE = "BLOOM"


class BrinIndex(PostgreSQLIndex):
    INDEX_TYPE = "BRIN"


class GinIndex(PostgreSQLIndex):
    INDEX_TYPE = "GIN"


class GistIndex(PostgreSQLIndex):
    INDEX_TYPE = "GIST"


class HashIndex(PostgreSQLIndex):
    INDEX_TYPE = "HASH"


class SpGistIndex(PostgreSQLIndex):
    INDEX_TYPE = "SPGIST"
