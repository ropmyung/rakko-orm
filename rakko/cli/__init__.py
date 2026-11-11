# Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
# Derived from Tortoise ORM; maintained and modified for Rakko ORM.
# SPDX-License-Identifier: Apache-2.0

"""Rakko CLI entry points."""

__all__ = ["main"]


def main() -> None:
    from rakko.cli.cli import main as cli_main

    cli_main()
