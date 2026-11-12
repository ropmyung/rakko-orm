# Modified for Rakko ORM: port package imports and internal references to the rakko namespace.

"""Rakko CLI entry points."""

__all__ = ["main"]


def main() -> None:
    from rakko.cli.cli import main as cli_main

    cli_main()
