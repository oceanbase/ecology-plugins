"""Haystack retriever components for OceanBaseDocumentStore."""

from typing import Any, Dict, List, Optional

from haystack import DeserializationError, Document, component, default_from_dict, default_to_dict
from haystack.dataclasses.sparse_embedding import SparseEmbedding

from oceanbase_haystack.document_store import OceanBaseDocumentStore, OceanBaseStoreError


@component
class OceanBaseEmbeddingRetriever:
    """Dense vector retrieval from ``OceanBaseDocumentStore`` (same role as ``MilvusEmbeddingRetriever``)."""

    def __init__(
        self, document_store: OceanBaseDocumentStore, filters: Optional[Dict[str, Any]] = None, top_k: int = 10
    ):
        self.filters = filters
        self.top_k = top_k
        self.document_store = document_store

    def to_dict(self) -> Dict[str, Any]:
        return default_to_dict(
            self, document_store=self.document_store.to_dict(), filters=self.filters, top_k=self.top_k
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OceanBaseEmbeddingRetriever":
        init_params = data.get("init_parameters", {})
        if "document_store" not in init_params:
            raise DeserializationError("Missing 'document_store' in serialization data")
        docstore = OceanBaseDocumentStore.from_dict(init_params["document_store"])
        data["init_parameters"]["document_store"] = docstore
        return default_from_dict(cls, data)

    @component.output_types(documents=List[Document])
    def run(
        self, query_embedding: List[float], top_k: Optional[int] = None, filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[Document]]:
        docs = self.document_store._embedding_retrieval(
            query_embedding=query_embedding,
            top_k=top_k or self.top_k,
            filters=filters or self.filters,
        )
        return {"documents": docs}


@component
class OceanBaseSparseEmbeddingRetriever:
    """Sparse vector ANN search; requires ``sparse_vector_field`` on the document store."""

    def __init__(
        self, document_store: OceanBaseDocumentStore, filters: Optional[Dict[str, Any]] = None, top_k: int = 10
    ):
        self.filters = filters
        self.top_k = top_k
        self.document_store = document_store

    def to_dict(self) -> Dict[str, Any]:
        return default_to_dict(
            self, document_store=self.document_store.to_dict(), filters=self.filters, top_k=self.top_k
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OceanBaseSparseEmbeddingRetriever":
        init_params = data.get("init_parameters", {})
        if "document_store" not in init_params:
            raise DeserializationError("Missing 'document_store' in serialization data")
        docstore = OceanBaseDocumentStore.from_dict(init_params["document_store"])
        data["init_parameters"]["document_store"] = docstore
        return default_from_dict(cls, data)

    @component.output_types(documents=List[Document])
    def run(
        self,
        query_sparse_embedding: Optional[SparseEmbedding] = None,
        query_text: Optional[str] = None,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, List[Document]]:
        if query_sparse_embedding is None:
            raise OceanBaseStoreError(
                "query_sparse_embedding is required; Milvus BM25 built-in sparse search is not supported."
            )
        docs = self.document_store._sparse_embedding_retrieval(
            query_sparse_embedding=query_sparse_embedding,
            top_k=top_k or self.top_k,
            filters=filters or self.filters,
            query_text=query_text,
        )
        return {"documents": docs}


@component
class OceanBaseHybridRetriever:
    """Dense + sparse hybrid retrieval using Reciprocal Rank Fusion (RRF), not pymilvus ``RRFRanker``."""

    def __init__(
        self,
        document_store: OceanBaseDocumentStore,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
        reranker: Any = None,
    ):
        self.filters = filters
        self.top_k = top_k
        self.document_store = document_store
        self.reranker = reranker

    def to_dict(self) -> Dict[str, Any]:
        return default_to_dict(
            self,
            document_store=self.document_store.to_dict(),
            filters=self.filters,
            top_k=self.top_k,
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OceanBaseHybridRetriever":
        init_params = data.get("init_parameters", {})
        if "document_store" not in init_params:
            raise DeserializationError("Missing 'document_store' in serialization data")
        docstore = OceanBaseDocumentStore.from_dict(init_params["document_store"])
        data["init_parameters"]["document_store"] = docstore
        return default_from_dict(cls, data)

    @component.output_types(documents=List[Document])
    def run(
        self,
        query_embedding: List[float],
        query_sparse_embedding: Optional[SparseEmbedding] = None,
        query_text: Optional[str] = None,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
    ):
        docs = self.document_store._hybrid_retrieval(
            query_embedding=query_embedding,
            query_sparse_embedding=query_sparse_embedding,
            filters=filters or self.filters,
            top_k=top_k or self.top_k,
            reranker=self.reranker,
            query_text=query_text,
        )
        return {"documents": docs}
