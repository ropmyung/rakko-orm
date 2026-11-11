# Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
# Derived from Tortoise ORM; maintained and modified for Rakko ORM.
# SPDX-License-Identifier: Apache-2.0

class TortoiseMigrationError(Exception):
    """Base migration error."""


class IncompatibleStateError(TortoiseMigrationError):
    """Raised when a migration operation can't be executed on a given State."""
