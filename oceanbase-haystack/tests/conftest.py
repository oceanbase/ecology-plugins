"""Shared pytest fixtures (mocked OceanBase client; no real DB)."""

from unittest.mock import MagicMock, patch

import pytest

from oceanbase_haystack.document_store import OceanBaseDocumentStore

from tests.constants import CONNECTION_ARGS, DEFAULT_INDEX_PARAMS


@pytest.fixture
def mock_obvector() -> MagicMock:
    m = MagicMock()
    m.check_table_exists.return_value = False
    return m


@pytest.fixture
def document_store(mock_obvector: MagicMock):
    """OceanBaseDocumentStore with ``ObVecClient`` fully mocked."""
    with patch.object(OceanBaseDocumentStore, "_create_client", return_value=mock_obvector):
        store = OceanBaseDocumentStore(
            collection_name="test_collection",
            connection_args=CONNECTION_ARGS,
            index_params=DEFAULT_INDEX_PARAMS,
        )
        yield store
