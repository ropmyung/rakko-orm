.. Modified for Rakko ORM: document the Rakko model/query API, project identity and development workflow.

Models and typing
=================

``Field[T]`` describes an instance value. Class access returns
``Query[ModelType, T]``; instance access returns ``T``.

.. code-block:: python

    from rakko import Field, Model, fields

    class User(Model):
        id: Field[int] = fields.AutoField()
        name: Field[str] = fields.CharField(100)
        age: Field[int | None] = fields.IntField(null=True)

    user = await User.create(name="Ada")
    await User.filter(User.id == user.id).update(age=21)

Constructor inference
---------------------

Only automatic integer factories remain ``dataclass_transform`` field
specifiers. Their ``init=False`` excludes generated IDs. Ordinary field
assignments make synthesized constructor parameters optional; field names,
value types and nullable types remain checked.

``ParamSpec`` preserves the constructor signature through query chains,
``create``, ``update`` and both upserts. It does not encode database-requiredness.
Runtime validation and DB constraints still determine valid saves.
``null=True`` allows ``None`` without requiring ``default=None``.

Metadata
--------

The ``@meta`` decorator converts a ``MetaOption`` declaration to the mapping
consumed by the model metaclass:

.. code-block:: python

    from rakko import Field, MetaOption, Model, fields
    from rakko.models import meta

    class User(Model):
        id: Field[int] = fields.AutoField()
        name: Field[str] = fields.CharField(100)

        @meta
        class Meta(MetaOption):
            table = "users"

Relations
---------

Foreign keys can receive model classes directly. ``@reverse_relation`` keeps
reverse accessors out of the constructor:

.. literalinclude:: ../examples/models.py
   :language: python

See :doc:`examples/basic` for joined loading and filtered prefetching.
