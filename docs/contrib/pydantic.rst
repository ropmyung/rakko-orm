.. Modified for Rakko ORM: document the Rakko model/query API, project identity and development workflow.

Pydantic
========

Pydantic helpers remain in ``rakko.contrib.pydantic``. The creator module
provides ``pydantic_model_creator`` and queryset-model creation helpers based
on runtime field metadata.

Model constructor ``ParamSpec`` hints and serialized schema requirements are
separate concerns. Recheck generated schemas after changing declarations,
relations or nullable fields. Integration coverage is being expanded alongside
the current model/query tests.
