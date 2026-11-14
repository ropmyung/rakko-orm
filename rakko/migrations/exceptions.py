# Modified for Rakko ORM: integrate migration components with Rakko models, imports and operation
# names.


class RakkoMigrationError(Exception):
    """Base migration error."""


class IncompatibleStateError(RakkoMigrationError):
    """Raised when a migration operation can't be executed on a given State."""
