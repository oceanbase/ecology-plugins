"""Live OceanBase tests; enabled only when ``OCEANBASE_CI=1`` (see ``.github/workflows/ci.yml``)."""

from __future__ import annotations

import os

import pytest
from haystack import Document

from oceanbase_haystack import OceanBaseDocumentStore, OceanBaseEmbeddingRetriever


def _ci_enabled() -> bool:
    v = os.environ.get("OCEANBASE_CI", "").strip().lower()
    return v in ("1", "true", "yes")


pytestmark = [
    pytest.mark.oceanbase,
    pytest.mark.skipif(not _ci_enabled(), reason="set OCEANBASE_CI=1 with a reachable OceanBase instance"),
]


DIM = 128


def test_live_write_and_dense_retrieve():
    connection_args = {
        "host": os.environ.get("OB_HOST", "127.0.0.1"),
        "port": os.environ.get("OB_PORT", "2881"),
        "user": os.environ.get("OB_USER", "root@test"),
        "password": os.environ.get("OB_PASSWORD", ""),
        "db_name": os.environ.get("OB_DB", "test"),
    }
    collection = os.environ.get("OB_COLLECTION", "haystack_ci_smoke")

    store = OceanBaseDocumentStore(
        collection_name=collection,
        connection_args=connection_args,
        index_params={"metric_type": "L2", "index_type": "HNSW", "params": {}},
        embedding_dim=DIM,
        drop_old=True,
    )

    store.write_documents(
        [
            Document(content="hello oceanbase ci", embedding=[0.1] * DIM, meta={"source": "ci"}),
        ]
    )

    retriever = OceanBaseEmbeddingRetriever(document_store=store, top_k=3)
    result = retriever.run(query_embedding=[0.1] * DIM)
    assert len(result["documents"]) >= 1
    assert any("hello" in (d.content or "") for d in result["documents"])
