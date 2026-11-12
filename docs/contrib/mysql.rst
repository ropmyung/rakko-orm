.. Modified for Rakko ORM: document the Rakko model/query API, project identity and development workflow.

MySQL extensions
================

The MySQL backend and retained extension modules live in
``rakko.backends.mysql`` and ``rakko.contrib.mysql``. Core integer fields support
``unsigned=True`` and explicit automatic factories; these are available from
``rakko.fields`` without a separate wrapper library.

See :doc:`../fields`, :doc:`../databases` and the SQL-only MySQL example in
:doc:`../examples/basic`. The current tests check schema/query rendering and
backend behavior with mocked clients, rather than claiming live-server coverage.
