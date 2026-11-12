.. Modified for Rakko ORM: document the Rakko model/query API, project identity and development workflow.

Validation
==========

Field validation and conversion run independently of static constructor hints.
A parameter being optional to Pyright does not mean that an omitted non-null
value is valid to save. ``rakko.validators`` retains the existing validator
classes for values, ranges, strings and related formats.

Use field options and validators to express runtime requirements. Catch
``rakko.exceptions.ValidationError`` for field validation failures. Database
integrity constraints remain enforced by the configured database.
