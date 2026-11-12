# Modified for Rakko ORM: port package imports and internal references to the rakko namespace.

"""Module entry point for `python -m tortoise`."""

from rakko.cli import main

if __name__ == "__main__":
    main()
