.. Modified for Rakko ORM: document the Rakko model/query API, project identity and development workflow.

Indexes
=======

The retained ``rakko.indexes.Index`` class describes named or expression
indexes. Field expressions can be supplied directly, for example
``Index(Member.name, name="idx_member_name")``. Metadata conversion resolves
field references using existing model metadata.

Query hint methods ``use_index`` and ``force_index`` accept index names as
strings; these are SQL index identifiers, not repeated model-field names.
Backend-specific index classes remain in ``rakko.contrib``. Validate persistent
index changes through the migration/schema tooling appropriate to your database.
