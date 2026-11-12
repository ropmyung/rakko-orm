.. Modified for Rakko ORM: document the Rakko model/query API, project identity and development workflow.

Fields
======

Declare instance values with ``Field[T]`` and metadata with ``fields`` factories.
Raw fields are declarations; SQL operators belong to class-level ``Query`` objects.

Integer families
----------------

.. list-table::
   :header-rows: 1

   * - Width
     - Ordinary field
     - Automatic factory
   * - 8 bit
     - ``TinyIntField``
     - ``TinyAutoField``
   * - 16 bit
     - ``SmallIntField``
     - ``SmallAutoField``
   * - 32 bit
     - ``IntField``
     - ``AutoField``
   * - 64 bit
     - ``BigIntField``
     - ``BigAutoField``

Use ``unsigned=True`` for unsigned ranges and MySQL UNSIGNED SQL. Automatic
factories enable generation. ``primary_key=True`` on an ordinary integer does
not imply generation, and ordinary integers have no ``auto_increment`` option.

.. code-block:: python

    id: Field[int] = fields.BigAutoField(unsigned=True)
    hits: Field[int] = fields.IntField(unsigned=True, default=0)

Nullable text and JSON
----------------------

Both Text and JSON support nullable values. For a specific JSON shape,
supply its generic type explicitly:

.. code-block:: python

    note: Field[str | None] = fields.TextField(null=True)
    preferences: Field[dict[str, str] | None] = fields.JSONField[
        dict[str, str] | None
    ](null=True)

``default`` is a Python initialization default. ``db_default`` is rendered
into schema SQL for evaluation by the database. Omitted nullable fields become
``None`` through the initialization path.

The retained field module also provides string, boolean, decimal, float,
binary, date/time, duration, UUID and enum fields. Backend-specific field
extensions live under ``rakko.contrib.mysql`` and ``rakko.contrib.postgres``.
