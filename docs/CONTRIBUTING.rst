.. Modified for Rakko ORM: document the Rakko model/query API, project identity and development workflow.

Contributing to Rakko ORM
=========================

Rakko is developed independently from Tortoise ORM. Direct changes and issue
reports to this project's maintainers and repository.

.. code-block:: console

    uv sync --all-groups --extra asyncpg --extra psycopg
    uv run --all-groups --extra asyncpg --extra psycopg pytest -q
    uv run --group test pyright rakko examples
    uv run --group docs sphinx-build -W --keep-going -b html docs docs/_build/html

Use Python 3.12+ with modern generics, PEP 8, four-space indentation and
explicit type hints. Preserve the distinction between declarations, SQL
expressions, runtime values and constructor signatures. Reuse PyPika and
backend infrastructure; avoid repeated metadata scans and speculative rewrites.

Add focused runtime tests for behavior changes and Pyright contracts for typing
changes. Keep examples executable. Distinguish fixes, API changes and planned work.

``rakko/`` contains the library, ``tests/`` runtime/typing tests,
``examples/`` runnable scripts, and ``docs/`` Sphinx sources. Preserve source
notices and upstream credits. See :doc:`CODE_OF_CONDUCT`.

``typings/`` supplies partial root export declarations for ``pypika_tortoise``.
Keep its ``py.typed`` marker set to ``partial`` so other upstream modules retain
their real types. Do not edit installed dependencies to fix local type errors;
CI installs the unmodified PyPI packages.

.. toctree::
   :hidden:

   CODE_OF_CONDUCT
