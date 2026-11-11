# Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
# Derived from Tortoise ORM; maintained and modified for Rakko ORM.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

from rakko.queryset import QuerySet


class Manager:
    """
    A Manager is the interface through which database query operations are provided to tortoise models.

    There is one default Manager for every tortoise model.
    """

    def __init__(self, model=None) -> None:
        self._model = model

    def get_queryset(self) -> QuerySet:
        if self._model is None:
            raise ValueError("Manager must be initialized with a model")

        return QuerySet(self._model)

    def __getattr__(self, item: str) -> Any:
        return getattr(self.get_queryset(), item)
