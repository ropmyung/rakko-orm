.. Modified for Rakko ORM: document the Rakko model/query API, project identity and development workflow.

.. _getting_started:

Getting started
===============

Use Python 3.12+ and run commands from this checkout. These instructions do
not assume a public Rakko package release.

.. code-block:: console

    uv sync --group test
    uv run -m examples.basic

The example uses isolated in-memory SQLite and closes connections on exit.

.. literalinclude:: ../examples/basic.py
   :language: python

The important distinctions
--------------------------

* ``Event.id`` is a query expression; ``event.id`` is a value.
* ``filter`` receives one criterion. Combine conditions with ``&``, ``|`` and ``~``.
* ``update`` changes only supplied fields.
* Regular constructor parameters are optional, while names/types remain checked.
  Runtime validation and database constraints still govern valid saves.
* An ordinary integer primary key does not imply auto-increment; use ``AutoField``.

Continue with :doc:`models`, :doc:`query`, :doc:`transactions` and
:doc:`examples/basic`. MySQL configuration is described in :doc:`databases`.
