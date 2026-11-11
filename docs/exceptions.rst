.. Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
   Derived from Tortoise ORM; maintained and modified for Rakko ORM.
   SPDX-License-Identifier: Apache-2.0

Exceptions
==========

Import exception classes from ``rakko.exceptions``. Common categories are:

* ``ConfigurationError`` for model/configuration problems.
* ``FieldError`` for invalid field references or ambiguous relation paths.
* ``ValidationError`` for invalid field values.
* ``DoesNotExist`` and ``MultipleObjectsReturned`` for single-record lookups.
* ``IntegrityError`` and ``OperationalError`` for translated database errors.
* ``ParamsError`` for invalid query parameters.

Upserts retry the same criterion after a uniqueness conflict. Validation or
unrelated integrity failures are not creation defaults; review the supplied
values and database constraints.
