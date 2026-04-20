"""Tests for Haystack retriever components (mocked document store)."""

from unittest.mock import MagicMock, patch

import pytest
from haystack import DeserializationError, Document

from oceanbase_haystack.document_store import OceanBaseDocumentStore, OceanBaseStoreError
from oceanbase_haystack.oceanbase_embedding_retriever import (
    OceanBaseEmbeddingRetriever,
    OceanBaseHybridRetriever,
    OceanBaseSparseEmbeddingRetriever,
)
from haystack.dataclasses.sparse_embedding import SparseEmbedding

from tests.constants import CONNECTION_ARGS, DEFAULT_INDEX_PARAMS


@pytest.fixture
def store(mock_obvector: MagicMock):
    with patch.object(OceanBaseDocumentStore, "_create_client", return_value=mock_obvector):
        s = OceanBaseDocumentStore(
            collection_name="t",
            connection_args=CONNECTION_ARGS,
            index_params=DEFAULT_INDEX_PARAMS,
        )
        yield s


def test_embedding_retriever_run_delegates(store: OceanBaseDocumentStore, mock_obvector: MagicMock):
    doc = Document(id="1", content="hi")
    with patch.object(store, "_embedding_retrieval", return_value=[doc]) as m:
        r = OceanBaseEmbeddingRetriever(document_store=store, top_k=3)
        out = r.run(query_embedding=[0.1, 0.2])
    m.assert_called_once()
    assert out["documents"] == [doc]


def test_embedding_retriever_top_k_override(store: OceanBaseDocumentStore):
    with patch.object(store, "_embedding_retrieval", return_value=[]) as m:
        r = OceanBaseEmbeddingRetriever(document_store=store, top_k=10)
        r.run(query_embedding=[0.1], top_k=2)
    assert m.call_args.kwargs["top_k"] == 2


def test_sparse_retriever_requires_query_sparse(mock_obvector: MagicMock):
    mock_obvector.check_table_exists.return_value = False
    with patch.object(OceanBaseDocumentStore, "_create_client", return_value=mock_obvector):
        with patch.object(OceanBaseDocumentStore, "_create_table_with_dim"):
            with patch.object(OceanBaseDocumentStore, "_reflect_table"):
                s = OceanBaseDocumentStore(
                    collection_name="t",
                    connection_args=CONNECTION_ARGS,
                    index_params=DEFAULT_INDEX_PARAMS,
                    sparse_vector_field="sparse_col",
                    embedding_dim=4,
                )
    r = OceanBaseSparseEmbeddingRetriever(document_store=s)
    with pytest.raises(OceanBaseStoreError, match="query_sparse_embedding"):
        r.run(query_sparse_embedding=None)


def test_hybrid_retriever_sparse_field_required(store: OceanBaseDocumentStore):
    r = OceanBaseHybridRetriever(document_store=store)
    with pytest.raises(OceanBaseStoreError, match="sparse_vector_field"):
        r.run(query_embedding=[0.1, 0.2])


def test_embedding_retriever_from_dict_missing_docstore():
    with pytest.raises(DeserializationError, match="document_store"):
        OceanBaseEmbeddingRetriever.from_dict(
            {
                "type": "OceanBaseEmbeddingRetriever",
                "init_parameters": {},
            }
        )


def test_embedding_retriever_to_dict_roundtrip(store: OceanBaseDocumentStore, mock_obvector: MagicMock):
    r = OceanBaseEmbeddingRetriever(document_store=store, top_k=5)
    data = r.to_dict()
    with patch.object(OceanBaseDocumentStore, "_create_client", return_value=mock_obvector):
        r2 = OceanBaseEmbeddingRetriever.from_dict(data)
    assert r2.top_k == 5


def test_hybrid_retriever_falls_back_to_dense_when_no_sparse(mock_obvector: MagicMock):
    mock_obvector.check_table_exists.return_value = False
    with patch.object(OceanBaseDocumentStore, "_create_client", return_value=mock_obvector):
        with patch.object(OceanBaseDocumentStore, "_create_table_with_dim"):
            with patch.object(OceanBaseDocumentStore, "_reflect_table"):
                s = OceanBaseDocumentStore(
                    collection_name="t",
                    connection_args=CONNECTION_ARGS,
                    index_params=DEFAULT_INDEX_PARAMS,
                    sparse_vector_field="sp",
                    embedding_dim=4,
                )
    doc = Document(id="a", content="x")
    with patch.object(s, "_embedding_retrieval", return_value=[doc]) as d_ret:
        with patch.object(s, "_sparse_embedding_retrieval") as s_ret:
            r = OceanBaseHybridRetriever(document_store=s)
            out = r.run(query_embedding=[0.1, 0.2], query_sparse_embedding=None)
    s_ret.assert_not_called()
    d_ret.assert_called_once()
    assert out["documents"] == [doc]


def test_hybrid_retriever_with_sparse_calls_rrf(mock_obvector: MagicMock):
    mock_obvector.check_table_exists.return_value = False
    with patch.object(OceanBaseDocumentStore, "_create_client", return_value=mock_obvector):
        with patch.object(OceanBaseDocumentStore, "_create_table_with_dim"):
            with patch.object(OceanBaseDocumentStore, "_reflect_table"):
                s = OceanBaseDocumentStore(
                    collection_name="t",
                    connection_args=CONNECTION_ARGS,
                    index_params=DEFAULT_INDEX_PARAMS,
                    sparse_vector_field="sp",
                    embedding_dim=4,
                )
    d1 = Document(id="1", content="a")
    d2 = Document(id="2", content="b")
    sp = SparseEmbedding(indices=[0], values=[1.0])
    with patch.object(s, "_embedding_retrieval", return_value=[d1]):
        with patch.object(s, "_sparse_embedding_retrieval", return_value=[d2]):
            r = OceanBaseHybridRetriever(document_store=s)
            out = r.run(query_embedding=[0.1], query_sparse_embedding=sp)
    assert len(out["documents"]) >= 1
