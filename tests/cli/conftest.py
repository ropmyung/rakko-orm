# Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
# Derived from Tortoise ORM; maintained and modified for Rakko ORM.
# SPDX-License-Identifier: Apache-2.0

import pytest


@pytest.fixture(scope="session", autouse=True)
def initialize_tests():
    return None
