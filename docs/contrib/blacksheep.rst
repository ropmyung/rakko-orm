.. Modified for Rakko ORM: document the Rakko model/query API, project identity and development workflow.

BlackSheep
==========

The retained adapter is provided by ``rakko.contrib.blacksheep``. Its
``register_tortoise`` helper initializes configured model modules and handles
connection cleanup through the framework lifecycle. Historical helper names
remain inside the independent Rakko package.

Use the field declarations and criteria from :doc:`../models` and
:doc:`../query`. Framework-specific executable examples are being rebuilt;
current working scripts are listed in :doc:`../examples/basic`.
