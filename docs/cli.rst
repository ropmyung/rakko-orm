.. Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
   Derived from Tortoise ORM; maintained and modified for Rakko ORM.
   SPDX-License-Identifier: Apache-2.0

Command-line tools
==================

The local package installs the ``rakko`` executable:

.. code-block:: console

    uv sync --group test
    uv run rakko --help

The retained command set includes ``init``, ``makemigrations``, ``migrate``,
``upgrade``, ``downgrade``, ``history``, ``heads``, ``sqlmigrate`` and ``shell``.
Consult command-specific help for options.

Configuration compatibility
---------------------------

The resolver still recognizes ``TORTOISE_ORM`` and the ``[tool.tortoise]`` /
``tortoise_orm`` configuration keys. These are retained names, not instructions
to install another ORM. Config objects live in ``rakko.config``.

The executable and help identify Rakko. No published repository or deployment
URL is assumed by the documentation. See :doc:`migration` for the migration
layer's adaptation/validation status.
