.. Modified for Rakko ORM: document the Rakko model/query API, project identity and development workflow.

Release preparation
===================

The source distribution includes ``RELEASING.md``, ``LICENSE_REVIEW.md`` and
``ASSETS.md`` with release commands, licensing decisions and artwork provenance.

This release is **1.0.0-alpha.2**, distributed as ``1.0.0a2``, and maintained by
**ropmyung**. The repository is https://github.com/ropmyung/rakko-orm; a documentation
site URL has not been assigned.

Preserve the original license, existing notices and contributor credits. New
changes to inherited files must retain a concise Rakko change notice and summary.
Project copyright information is maintained in ``NOTICE.txt``; repeated
copyright and SPDX banners are not required in source files.
The wheel and source archive both include the licensing and attribution files.
Publishing uses the manually dispatched ``pypi.yml`` workflow; its default is
build-only. Configure the actual repository as a Trusted Publisher before
selecting a publishing target. Documentation deployment uses this repository's
GitHub Pages, without an upstream destination.

See :doc:`license` and :doc:`CHANGELOG` for licensing text and release changes.
