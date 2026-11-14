.. Modified for Rakko ORM: document the Rakko model/query API, project identity and development workflow.

Database migrations
===================

Rakko migrations snapshot model fields and metadata, generate Python operations,
and apply or reverse them through the configured database backend. Generated
files import ``rakko`` and preserve automatic integer fields and UNSIGNED flags.
History is stored in ``rakko_migrations``.

Configure and run
-----------------

In ``settings.py`` define ``RAKKO_ORM`` using the ordinary connections/apps
configuration. Include a migrations package for each app:

.. code-block:: python

    RAKKO_ORM = {
        "connections": {"default": "sqlite://database.sqlite3"},
        "apps": {
            "models": {
                "models": ["app.models"],
                "migrations": "app.migrations",
            }
        },
    }

Set ``RAKKO_ORM=settings.RAKKO_ORM`` in the environment, pass
``-c settings.RAKKO_ORM``, or configure the module path in ``pyproject.toml``:

.. code-block:: toml

    [tool.rakko]
    rakko_orm = "settings.RAKKO_ORM"

.. code-block:: console

    uv run rakko init
    uv run rakko makemigrations
    uv run rakko sqlmigrate models 0001_initial
    uv run rakko migrate --dry-run
    uv run rakko migrate
    uv run rakko history
    uv run rakko heads
    uv run rakko downgrade models 0001_initial
    uv run rakko upgrade models

``downgrade models`` without a target reverses every migration in that app.
``--fake`` updates history without running operations. ``--dry-run`` does not
create the recorder table or change migration history. ``sqlmigrate --backward``
prints reverse SQL. Use an actual generated migration name for each target.

Expression constraints
----------------------

Conditions accept PyPika criteria, including Rakko's typed comparisons. SQL
strings and Python booleans are rejected. Within a model declaration, a callback
receives the model class after its field descriptors have been constructed:

.. code-block:: python

    from rakko import Field, Model, fields
    from rakko.indexes import Index
    from rakko.migrations.constraints import CheckConstraint, UniqueConstraint
    from rakko.models import MetaOption

    class Account(Model):
        id: Field[int] = fields.AutoField()
        balance: Field[int] = fields.IntField(source_field="stored_balance")
        label: Field[str] = fields.CharField(100)

        Meta = MetaOption(
            table="accounts",
            constraints=[
                CheckConstraint(
                    check=lambda model: model.balance >= 0,
                    name="nonnegative_balance",
                ),
                UniqueConstraint(fields=(label,), name="unique_label"),
            ],
            indexes=[Index(fields=(balance,), name="balance_idx")],
        )

``@meta class Meta(MetaOption)`` is also supported. In that nested class, use
``lambda model: model.balance >= 0`` for the condition: the outer model class does
not exist yet while its body executes. Fields in ``UniqueConstraint`` and
``Index(fields=...)`` can be field references. Serialized migration snapshots
use historical names and native PyPika nodes, without importing live models.
Column aliases are resolved from existing field metadata.

With ``Meta = MetaOption(...)``, ``@Meta.check_constraint`` can register a
callback taking the model class. The function name becomes the constraint name.
Callable checks must be resolved with ``constraint.resolve(model)`` before
serialization; migration snapshots perform this step automatically.

Conditional unique constraints take ``condition=lambda model: model.balance > 0``.
They are supported by PostgreSQL and SQLite; MySQL reports them as unsupported.
Conditions cannot traverse joins. Snapshot expression serialization supports
comparisons, boolean combinations, arithmetic, ranges, membership, NULL checks
and ordinary SQL functions. Unsupported expression node types raise an error
instead of silently embedding SQL for a different dialect.

Validation and existing files
-----------------------------

Tests cover SQLite, MySQL 8.4 (aiomysql/asyncmy) and PostgreSQL 16
(asyncpg/psycopg), including creation, changes, reversal, data preservation,
constraints, history and SQL preview. SQLite rebuilds preserve related rows,
constraints and indexes; foreign keys are checked before committing atomic
migrations. For atomic migrations on transactional-DDL backends, schema changes and migration
records are committed together. MySQL DDL can commit implicitly; it cannot provide the
same rollback guarantee.

SQL Server and Oracle editors remain available but are not covered by this
live-database matrix. Review operations and SQL for those backends separately.

Files generated before these fixes may import the old package or contain
ordinary integer fields where automatic fields were intended. Regenerate such
files only if they have not been applied. Keep already applied history intact
and plan a separate repair migration after checking the existing database.
The former ``tortoise_migrations`` history table is not adopted automatically;
Rakko uses its own history and configuration names.
