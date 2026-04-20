# Local workflows aligned with ecology-plugins CI (see repo .github/workflows/workflow.yml and oceanbase-haystack-ci.yml).

.PHONY: help install check test test-ci build

help:
	@echo "Targets: install | check (ruff) | test (all pytest) | test-ci (exclude live OB) | build"

install:
	python3 -m pip install -e ".[dev]"

check:
	python3 -m ruff check src tests
	python3 -m ruff format --check src tests

test:
	python3 -m pytest tests -v

test-ci:
	python3 -m pytest tests -v -m "not oceanbase"

build:
	python3 -m build
