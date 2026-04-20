"""Unit tests for ``OceanBaseDocumentStore`` helpers (mocked DB)."""

from unittest.mock import MagicMock, patch

import pytest
from haystack import Document
from haystack.dataclasses.sparse_embedding import SparseEmbedding

from oceanbase_haystack.document_store import (
    OceanBaseDocumentStore,
    OceanBaseStoreError,
    _distance_fn,
    _rrf_merge,
)
from tests.constants import CONNECTION_ARGS, DEFAULT_INDEX_PARAMS


def test_rrf_merge_orders_by_fusion_score():
    d1 = Document(id="a", content="a")
    d2 = Document(id="b", content="b")
    d3 = Document(id="c", content="c")
    out = _rrf_merge([[d1, d2], [d2, d3]], top_k=2)
    assert len(out) == 2
    assert all(hasattr(d, "score") for d in out)


def test_distance_fn_l2_inner_cosine():
    assert _distance_fn("l2") is not None
    assert _distance_fn("inner_product") is not None
    assert _distance_fn("cosine") is not None


def test_distance_fn_unsupported():
    with pytest.raises(OceanBaseStoreError, match="Unsupported metric"):
        _distance_fn("unknown_metric")


def test_builtin_function_not_supported():
    with pytest.raises(OceanBaseStoreError, match="builtin_function"):
        OceanBaseDocumentStore(
            connection_args=CONNECTION_ARGS,
            index_params=DEFAULT_INDEX_PARAMS,
            builtin_function=object(),
        )


def test_invalid_index_type():
    mock_ob = MagicMock()
    with patch.object(OceanBaseDocumentStore, "_create_client", return_value=mock_ob):
        with pytest.raises(OceanBaseStoreError, match="index_type"):
            OceanBaseDocumentStore(
                connection_args=CONNECTION_ARGS,
                index_params=DEFAULT_INDEX_PARAMS,
                index_type="NOT_A_REAL_INDEX",
            )


def test_count_documents_no_table(document_store: OceanBaseDocumentStore, mock_obvector: MagicMock):
    mock_obvector.check_table_exists.return_value = False
    assert document_store.count_documents() == 0


def test_filter_documents_no_table(document_store: OceanBaseDocumentStore, mock_obvector: MagicMock):
    mock_obvector.check_table_exists.return_value = False
    assert document_store.filter_documents() == []


def test_write_documents_empty_returns_zero(document_store: OceanBaseDocumentStore):
    # Empty input still calls ``_ensure_table`` before building rows; avoid real DDL on the mock.
    with patch.object(document_store, "_ensure_table"):
        assert document_store.write_documents([]) == 0


def test_delete_documents_empty_noop(document_store: OceanBaseDocumentStore):
    document_store.delete_documents([])


def test_normalize_vec(document_store: OceanBaseDocumentStore):
    v = [3.0, 4.0]
    out = document_store._normalize_vec(v)
    assert abs(sum(x * x for x in out) - 1.0) < 1e-6


def test_normalize_vec_zero_norm(document_store: OceanBaseDocumentStore):
    assert document_store._normalize_vec([0.0, 0.0]) == [0.0, 0.0]


def test_parse_vector_list(document_store: OceanBaseDocumentStore):
    assert document_store._parse_vector([1.0, 2.0]) == [1.0, 2.0]


def test_parse_vector_none(document_store: OceanBaseDocumentStore):
    assert document_store._parse_vector(None) is None


def test_sparse_to_ob(document_store: OceanBaseDocumentStore):
    sp = SparseEmbedding(indices=[0, 2], values=[0.5, 1.5])
    d = document_store._sparse_to_ob(sp)
    assert d == {0: 0.5, 2: 1.5}


def test_discard_invalid_meta_drops_non_json_values(document_store: OceanBaseDocumentStore):
    doc = Document(id="1", content="x", embedding=[0.1, 0.2], meta={"ok": 1, "bad": object()})
    OceanBaseDocumentStore._discard_invalid_meta(doc)
    assert "bad" not in (doc.meta or {})
    assert doc.meta.get("ok") == 1


def test_select_score_fn_l2(document_store: OceanBaseDocumentStore):
    document_store.vidx_metric_type = "l2"
    fn = document_store._select_score_fn()
    assert fn(0.0) == 1.0


def test_select_score_fn_inner_product(document_store: OceanBaseDocumentStore):
    document_store.vidx_metric_type = "inner_product"
    fn = document_store._select_score_fn()
    assert fn(1.0) == 1.0


def test_to_dict_from_dict_roundtrip(document_store: OceanBaseDocumentStore, mock_obvector: MagicMock):
    data = document_store.to_dict()
    with patch.object(OceanBaseDocumentStore, "_create_client", return_value=mock_obvector):
        restored = OceanBaseDocumentStore.from_dict(data)
    assert restored.collection_name == document_store.collection_name
    assert restored.connection_args["host"] == CONNECTION_ARGS["host"]
