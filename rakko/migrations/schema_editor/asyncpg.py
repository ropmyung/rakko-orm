# Modified for Rakko ORM: integrate migration components with Rakko models, imports and operation
# names.

from __future__ import annotations

from rakko.migrations.schema_editor.base_postgres import BasePostgresSchemaEditor


class AsyncpgSchemaEditor(BasePostgresSchemaEditor):
    pass
