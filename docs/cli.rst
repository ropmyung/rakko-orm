.. Modified for Rakko ORM: document the Rakko model/query API, project identity and development workflow.

Command-line tools
==================

The local package installs the ``rakko`` executable:

.. code-block:: console

    uv sync --group test
    uv run rakko --help

The retained command set includes ``init``, ``makemigrations``, ``migrate``,
``upgrade``, ``downgrade``, ``history``, ``heads``, ``sqlmigrate`` and ``shell``.
Consult command-specific help for options.

Configuration
-------------

Use ``RAKKO_ORM`` and ``[tool.rakko]`` / ``rakko_orm`` for automatic configuration
lookup. ``-c module.VARIABLE`` accepts an explicit config variable; JSON and YAML
config files are accepted with ``--config-file``. The typed configuration class
is ``rakko.config.RakkoConfig``.

Migration records live in ``rakko_migrations``. Shell helpers expose ``Rakko``
and ``rakko``; install the optional ``ipython`` or ``ptpython`` extra for a shell.
On Windows the CLI uses a selector event loop, which also supports psycopg.
See :doc:`migration` for the complete migration workflow and validation scope.
