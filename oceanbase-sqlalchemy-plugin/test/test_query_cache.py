"""Reflection query caches belong to each dialect's lifecycle."""

import gc
import sys
import types
import weakref
from unittest import mock

import pytest
import sqlalchemy as sa

pytestmark = pytest.mark.skipif(
    not sa.__version__.startswith("2."),
    reason="Dictionary query builders are used by SQLAlchemy 2.x",
)


@pytest.fixture
def dialect_class():
    with mock.patch.dict(
        sys.modules, {"cx_Oceanbase": types.ModuleType("cx_Oceanbase")}
    ):
        from oceanbase_sqlalchemy.cx_oracle import OceanBaseDialect_cx_oracle

        yield OceanBaseDialect_cx_oracle


@pytest.mark.parametrize("method", ["_constraint_query", "_index_query"])
def test_query_cache_isolated_by_owner_and_dialect(dialect_class, method):
    first = dialect_class()
    second = dialect_class()
    query = getattr(first, method)("OWNER_A")

    assert getattr(first, method)("OWNER_A") is query
    assert getattr(first, method)("OWNER_B") is not query
    assert getattr(second, method)("OWNER_A") is not query


@pytest.mark.parametrize("method", ["_constraint_query", "_index_query"])
def test_query_cache_bounded_per_dialect(dialect_class, method):
    first = dialect_class()
    second = dialect_class()
    first_query = getattr(first, method)("OWNER_A")
    oldest_query = getattr(second, method)("OWNER_0")
    for index in range(1, 129):
        getattr(second, method)("OWNER_" + str(index))

    # A busy dialect evicts its own oldest query, without evicting other
    # dialects' cached queries.
    assert getattr(first, method)("OWNER_A") is first_query
    assert getattr(second, method)("OWNER_0") is not oldest_query


@pytest.mark.parametrize(
    "method, use_parent_query",
    [("_constraint_query", False), ("_index_query", False), ("_index_query", True)],
)
def test_query_cache_does_not_retain_dialect(
    dialect_class, method, use_parent_query, monkeypatch
):
    if use_parent_query:
        monkeypatch.setattr(
            sys.modules[dialect_class.__module__],
            "_dictionary_has_ind_expressions",
            False,
        )

    def cached_dialect_reference():
        dialect = dialect_class()
        getattr(dialect, method)("OWNER_A")
        return weakref.ref(dialect)

    reference = cached_dialect_reference()
    gc.collect()

    assert reference() is None
