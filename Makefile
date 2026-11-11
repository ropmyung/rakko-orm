# Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
# Derived from Tortoise ORM; maintained and modified for Rakko ORM.
# SPDX-License-Identifier: Apache-2.0

checkfiles = rakko/ examples/ tests/ conftest.py
py_warn = PYTHONDEVMODE=1
pytest_opts = -n auto --cov=rakko --cov-append --cov-branch --tb=native -q -m "not benchmark"
release_dir = dist/releases/1.0.0a0

TORTOISE_MYSQL_PASS ?= 123456
TORTOISE_POSTGRES_PASS ?= 123456
TORTOISE_MSSQL_PASS ?= 123456
TORTOISE_ORACLE_PASS ?= 123456

help:
	@echo  "Rakko ORM development makefile"
	@echo
	@echo  "usage: make <target>"
	@echo  "Targets:"
	@echo  "    up      Updates dev/test dependencies"
	@echo  "    deps    Ensure dev/test dependencies are installed"
	@echo  "    check   Checks that build is sane"
	@echo  "    test    Runs all tests"
	@echo  "    docs    Builds the documentation"
	@echo  "    style   Auto-formats the code"
	@echo  "    lint    Auto-formats the code and check type hints"

up:
	uv lock --upgrade

deps:
	uv sync --reinstall-package rakko-orm --frozen --all-groups --extra asyncpg --extra accel --extra psycopg --extra asyncodbc --extra aiomysql $(options)

deps_with_asyncmy:
	uv sync --reinstall-package rakko-orm --frozen --all-groups --extra asyncpg --extra accel --extra psycopg --extra asyncodbc --extra asyncmy $(options)

check: build _check
_check:
	uv run --frozen ruff format --check $(checkfiles) || (echo "Please run 'make style' to auto-fix style issues" && false)
	uv run --frozen ruff check $(checkfiles)
	#pylint -d C,W,R $(checkfiles)
	$(MAKE) _codeqc

style: deps _style
_style:
	uv run --frozen ruff format $(checkfiles)
	uv run --frozen ruff check --fix $(checkfiles)

lint: build _lint
_lint:
	$(MAKE) _style
	$(MAKE) _codeqc

codeqc: build _codeqc
_codeqc:
	uv run --frozen mypy $(checkfiles)
	uv run --frozen bandit -c pyproject.toml -r $(checkfiles)
	uv run --no-sync twine check --strict $(release_dir)/*.whl $(release_dir)/*.tar.gz

test: deps
	$(py_warn) TORTOISE_TEST_DB=sqlite://:memory: uv run --frozen pytest $(pytest_opts)

test_fast: deps
	$(py_warn) TORTOISE_TEST_DB=sqlite://:memory: uv run --frozen pytest -n auto --tb=native -q

test_sqlite:
	$(py_warn) TORTOISE_TEST_DB=sqlite://:memory: uv run --frozen pytest --cov-report= $(pytest_opts)

test_sqlite_regexp:
	$(py_warn) TORTOISE_TEST_DB=sqlite://:memory:?install_regexp_functions=True uv run --frozen pytest --cov-report= $(pytest_opts)

test_postgres_asyncpg:
	uv run --frozen python -V | grep PyPy || $(py_warn) TORTOISE_TEST_DB="asyncpg://postgres:$(TORTOISE_POSTGRES_PASS)@127.0.0.1:5432/test_\{\}" uv run --frozen pytest $(pytest_opts) --cov-report=

test_postgres_psycopg:
	uv run --frozen python -V | grep PyPy || $(py_warn) TORTOISE_TEST_DB="psycopg://postgres:$(TORTOISE_POSTGRES_PASS)@127.0.0.1:5432/test_\{\}" uv run --frozen pytest $(pytest_opts) --cov-report=

test_mysql_myisam:
	$(py_warn) TORTOISE_TEST_DB="mysql://root:$(TORTOISE_MYSQL_PASS)@127.0.0.1:3306/test_\{\}?storage_engine=MYISAM" uv run --frozen pytest $(pytest_opts) --cov-report=

test_mysql:
	$(py_warn) TORTOISE_TEST_DB="mysql://root:$(TORTOISE_MYSQL_PASS)@127.0.0.1:3306/test_\{\}" uv run --frozen pytest $(pytest_opts) --cov-report=

test_mysql_asyncmy:
	$(MAKE) deps_with_asyncmy
	$(MAKE) test_mysql
	# Restore dependencies to the default
	$(MAKE) deps

test_mssql:
	$(py_warn) TORTOISE_TEST_DB="mssql://sa:$(TORTOISE_MSSQL_PASS)@127.0.0.1:1433/test_\{\}?driver=$(TORTOISE_MSSQL_DRIVER)&TrustServerCertificate=YES" uv run --frozen pytest $(pytest_opts) --cov-report=

test_oracle:
	$(py_warn) TORTOISE_TEST_DB="oracle://SYSTEM:$(TORTOISE_ORACLE_PASS)@127.0.0.1:1521/test_\{\}?driver=$(TORTOISE_ORACLE_DRIVER)" uv run --frozen pytest $(pytest_opts) --cov-report=

_testall: test_sqlite test_postgres_asyncpg test_postgres_psycopg test_mysql_myisam test_mysql test_mysql_asyncmy test_mssql

	uv run --frozen coverage report

testall: deps _testall

ci: check _testall

docs:
	uv run --group docs sphinx-build -W --keep-going -b html docs docs/_build/html

build:
	uv build --out-dir $(release_dir)

publish: build
	uv run --no-sync twine check --strict $(release_dir)/*.whl $(release_dir)/*.tar.gz
	uv run --no-sync twine upload $(release_dir)/*.whl $(release_dir)/*.tar.gz
