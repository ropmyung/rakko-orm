# Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
# Derived from Tortoise ORM; maintained and modified for Rakko ORM.
# SPDX-License-Identifier: Apache-2.0

from pypika_tortoise.terms import Function


class Random(Function):
    """
    Generate random number.

    :samp:`Random()`
    """

    def __init__(self, alias=None) -> None:
        super().__init__("RANDOM", alias=alias)
