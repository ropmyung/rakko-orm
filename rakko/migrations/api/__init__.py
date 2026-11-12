# Modified for Rakko ORM: integrate migration components with Rakko models, imports and operation
# names.

"""Migration API (experimental).

Integration note: the migration API initializes apps without eagerly creating
database clients by calling ``Rakko.init(..., init_connections=False)``.
Connections are created lazily when the executor requests them.
"""

from rakko.migrations.api.migrate import migrate
from rakko.migrations.api.plan import plan
from rakko.migrations.api.sqlmigrate import sqlmigrate

__all__ = ["migrate", "plan", "sqlmigrate"]
