.. Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
   Derived from Tortoise ORM; maintained and modified for Rakko ORM.
   SPDX-License-Identifier: Apache-2.0

Static typing and linters
=========================

Pyright/Pylance understand ``Field[T]`` class/instance access and the
constructor signatures preserved by ``ParamSpec``. Tests in
``tests/typing_queries.py`` and ``tests/test_typing.py`` exercise those contracts.

.. code-block:: console

    uv run --group test pyright rakko examples

Legacy Pylint transforms remain in the source but are not the mechanism that
provides Rakko's type safety. Custom managers and application schemas need
explicit annotations; retain tests for those integration boundaries.
