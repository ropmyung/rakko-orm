# Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
# Derived from Tortoise ORM; maintained and modified for Rakko ORM.
# SPDX-License-Identifier: Apache-2.0

from pypika_tortoise.terms import Function, Term


class ToTsVector(Function):
    """
    to to_tsvector function
    """

    def __init__(self, field: Term) -> None:
        super().__init__("TO_TSVECTOR", field)


class ToTsQuery(Function):
    """
    to_tsquery function
    """

    def __init__(self, field: Term) -> None:
        super().__init__("TO_TSQUERY", field)


class PlainToTsQuery(Function):
    """
    plainto_tsquery function
    """

    def __init__(self, field: Term) -> None:
        super().__init__("PLAINTO_TSQUERY", field)


class Random(Function):
    """
    Generate random number.

    :samp:`Random()`
    """

    def __init__(self, alias=None) -> None:
        super().__init__("RANDOM", alias=alias)
