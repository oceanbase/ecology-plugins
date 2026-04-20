"""OceanBase-backed Haystack document store (pyobvector / SQL vector table)."""

import json
import logging
import math
from copy import deepcopy
from typing import Any, Callable, Dict, List, Optional

from haystack import Document, default_from_dict, default_to_dict
from haystack.dataclasses.sparse_embedding import SparseEmbedding
from haystack.document_stores.errors import DocumentStoreError
from haystack.document_stores.types import DuplicatePolicy
from haystack.errors import FilterError
from haystack.utils import Secret, deserialize_secrets_inplace
from pyobvector import (
    SPARSE_VECTOR,
    VECTOR,
    ObVecClient,
    VecIndexType,
    cosine_distance,
    inner_product,
    l2_distance,
)
from sqlalchemy import JSON, Column, String, Table, text
from sqlalchemy.dialects.mysql import LONGTEXT

from oceanbase_haystack.filters import parse_filters_to_sql
from oceanbase_haystack.utils.constant import META_FIELD, PRIMARY_FIELD, TEXT_FIELD, VECTOR_FIELD, EmbeddingMode

logger = logging.getLogger(__name__)


class OceanBaseStoreError(DocumentStoreError):
    pass


DEFAULT_OCEANBASE_CONNECTION: Dict[str, Any] = {
    "host": "localhost",
    "port": "2881",
    "user": "root@test",
    "password": "",
    "db_name": "test",
}

MAX_LIMIT_SIZE = 10_000

OCEANBASE_SUPPORTED_VECTOR_INDEX_TYPES = {
    "HNSW": VecIndexType.HNSW,
    "HNSW_SQ": VecIndexType.HNSW_SQ,
    "IVF": VecIndexType.IVFFLAT,
    "IVF_FLAT": VecIndexType.IVFFLAT,
    "IVF_SQ": VecIndexType.IVFSQ,
    "IVF_PQ": VecIndexType.IVFPQ,
    "FLAT": VecIndexType.IVFFLAT,
}

DEFAULT_OCEANBASE_HNSW_BUILD_PARAM = {"M": 16, "efConstruction": 200}
DEFAULT_OCEANBASE_IVF_BUILD_PARAM = {"nlist": 128}
DEFAULT_OCEANBASE_HNSW_SEARCH_PARAM = {"efSearch": 64}


def _map_metric_to_ob(metric_type: Optional[str]) -> str:
    if not metric_type:
        return "l2"
    mt = str(metric_type).upper()
    if mt == "L2":
        return "l2"
    if mt in ("IP", "INNER_PRODUCT"):
        return "inner_product"
    if mt == "COSINE":
        return "cosine"
    return "l2"


def _map_index_type_name(milvus_index: Optional[str]) -> str:
    if not milvus_index:
        return "HNSW"
    it = str(milvus_index).upper()
    if it in ("AUTOINDEX", "SCANN", "ANNOY"):
        return "HNSW"
    if it in OCEANBASE_SUPPORTED_VECTOR_INDEX_TYPES:
        return it
    return "HNSW"


def _distance_fn(metric: str) -> Callable[..., Any]:
    m = metric.lower()
    if m == "l2":
        return l2_distance
    if m == "inner_product":
        return inner_product
    if m == "cosine":
        return cosine_distance
    raise OceanBaseStoreError(f"Unsupported metric: {metric}")


def _rrf_merge(
    ranked_lists: List[List[Document]],
    k: int = 60,
    top_k: int = 10,
) -> List[Document]:
    scores: Dict[str, float] = {}
    by_id: Dict[str, Document] = {}
    for docs in ranked_lists:
        for rank, doc in enumerate(docs):
            by_id[doc.id] = doc
            scores[doc.id] = scores.get(doc.id, 0.0) + 1.0 / (k + rank + 1)
    ordered = sorted(scores.keys(), key=lambda i: scores[i], reverse=True)
    out: List[Document] = []
    for doc_id in ordered[:top_k]:
        d = by_id[doc_id]
        d.score = scores[doc_id]
        out.append(d)
    return out


class OceanBaseDocumentStore:
    """
    Haystack document store backed by an OceanBase vector table.

    The API follows milvus-haystack conventions; connectivity and DDL use pyobvector's ``ObVecClient``.
    """

    def __init__(
        self,
        collection_name: str = "HaystackCollection",
        connection_args: Optional[Dict[str, Any]] = None,
        *,
        drop_old: bool = False,
        primary_field: str = PRIMARY_FIELD,
        text_field: str = TEXT_FIELD,
        vector_field: str = VECTOR_FIELD,
        meta_field: str = META_FIELD,
        sparse_vector_field: Optional[str] = None,
        index_params: Optional[dict] = None,
        search_params: Optional[dict] = None,
        vidx_name: str = "haystack_vidx",
        normalize: bool = False,
        embedding_dim: Optional[int] = None,
        vidx_metric_type: Optional[str] = None,
        index_type: Optional[str] = None,
        vidx_algo_params: Optional[Dict[str, Any]] = None,
        builtin_function: Any = None,
        **kwargs: Any,
    ) -> None:
        if builtin_function:
            raise OceanBaseStoreError(
                "builtin_function (e.g. Milvus BM25) is not supported on OceanBase; "
                "use a sparse embedding model and pass SparseEmbedding instead."
            )

        self.collection_name = collection_name
        self.connection_args = connection_args or DEFAULT_OCEANBASE_CONNECTION.copy()
        self.drop_old = drop_old
        self._primary_field = primary_field
        self._text_field = text_field
        self._vector_field = vector_field
        self._meta_field = meta_field
        self._sparse_vector_field = sparse_vector_field
        self.index_params = index_params
        self.search_params = search_params or {}
        self.vidx_name = vidx_name
        self.normalize = normalize
        self._embedding_dim = embedding_dim
        self._sparse_mode = EmbeddingMode.EMBEDDING_MODEL if sparse_vector_field else None

        ip = index_params or {}
        self.vidx_metric_type = vidx_metric_type or _map_metric_to_ob(ip.get("metric_type"))
        self.index_type = (index_type or _map_index_type_name(ip.get("index_type"))).upper()
        if self.index_type not in OCEANBASE_SUPPORTED_VECTOR_INDEX_TYPES:
            raise OceanBaseStoreError(
                f"index_type must be one of {list(OCEANBASE_SUPPORTED_VECTOR_INDEX_TYPES.keys())}, got {self.index_type}"
            )

        if vidx_algo_params is not None:
            self.vidx_algo_params = dict(vidx_algo_params)
        elif ip.get("params"):
            self.vidx_algo_params = dict(ip["params"])
        else:
            if self.index_type in ("HNSW", "HNSW_SQ"):
                self.vidx_algo_params = dict(DEFAULT_OCEANBASE_HNSW_BUILD_PARAM)
            elif self.index_type.startswith("IVF") or self.index_type == "FLAT":
                self.vidx_algo_params = dict(DEFAULT_OCEANBASE_IVF_BUILD_PARAM)
            else:
                self.vidx_algo_params = {}

        if self.index_type == "IVF_PQ" and "m" not in self.vidx_algo_params:
            self.vidx_algo_params["m"] = 3

        self._ob_extra_kwargs = kwargs
        self._obvector = self._create_client()
        self.hnsw_ef_search = -1
        self._dummy_value = 999.0
        self._table_loaded = False

        if drop_old:
            self._obvector.drop_table_if_exist(self.collection_name)

        if self._obvector.check_table_exists(self.collection_name):
            self._reflect_table()
        elif embedding_dim is not None:
            self._create_table_with_dim(int(embedding_dim))
            self._reflect_table()

    def _create_client(self) -> ObVecClient:
        ca = self.connection_args
        host = ca.get("host", "localhost")
        port = str(ca.get("port", "2881"))
        user = ca.get("user", "root@test")
        password = ca.get("password", "")
        db_name = ca.get("db_name", "test")
        return ObVecClient(
            uri=f"{host}:{port}",
            user=user,
            password=password,
            db_name=db_name,
            **self._ob_extra_kwargs,
        )

    def _reflect_table(self) -> None:
        table = Table(
            self.collection_name,
            self._obvector.metadata_obj,
            autoload_with=self._obvector.engine,
        )
        names = [c.name for c in table.columns]
        if self._primary_field not in names or self._vector_field not in names:
            raise OceanBaseStoreError(
                f"Table {self.collection_name} columns do not match primary_field/vector_field config: {names}"
            )
        self._table_loaded = True

    def _create_table_with_dim(self, dim: int) -> None:
        cols = [
            Column(self._primary_field, String(4096), primary_key=True, autoincrement=False),
            Column(self._vector_field, VECTOR(dim)),
            Column(self._text_field, LONGTEXT),
            Column(self._meta_field, JSON),
        ]

        vidx_params = self._obvector.prepare_index_params()
        vidx_params.add_index(
            field_name=self._vector_field,
            index_type=OCEANBASE_SUPPORTED_VECTOR_INDEX_TYPES[self.index_type],
            index_name=self.vidx_name,
            metric_type=self.vidx_metric_type,
            params=self.vidx_algo_params,
        )

        if self._sparse_vector_field:
            cols.append(Column(self._sparse_vector_field, SPARSE_VECTOR()))
            sparse_kwargs: Dict[str, Any] = {}
            if getattr(self._obvector, "_is_seekdb", lambda: False)():
                sparse_kwargs["sparse_index_type"] = "sindi"
            vidx_params.add_index(
                field_name=self._sparse_vector_field,
                index_type=VecIndexType.DAAT,
                index_name=f"{self.vidx_name}_sparse",
                metric_type="inner_product",
                **sparse_kwargs,
            )

        self._obvector.create_table_with_index_params(
            table_name=self.collection_name,
            columns=cols,
            indexes=None,
            vidxs=vidx_params,
            fts_idxs=None,
            partitions=None,
        )

    def _ensure_table(self, embedding_dim: int) -> None:
        if self._obvector.check_table_exists(self.collection_name):
            if not self._table_loaded:
                self._reflect_table()
            return
        self._create_table_with_dim(embedding_dim)
        self._reflect_table()

    @property
    def client(self) -> ObVecClient:
        return self._obvector

    def _handle_hnsw_ef_search(self) -> None:
        sp = self.search_params or DEFAULT_OCEANBASE_HNSW_SEARCH_PARAM
        ef = sp.get("efSearch", DEFAULT_OCEANBASE_HNSW_SEARCH_PARAM.get("efSearch", 64))
        if self.index_type in ("HNSW", "HNSW_SQ") and ef != self.hnsw_ef_search:
            self._obvector.set_ob_hnsw_ef_search(ef)
            self.hnsw_ef_search = ef

    def count_documents(self) -> int:
        if not self._obvector.check_table_exists(self.collection_name):
            return 0
        sql = f"SELECT COUNT(*) AS c FROM `{self.collection_name}`"
        with self._obvector.engine.connect() as conn:
            row = conn.execute(text(sql)).fetchone()
        return int(row[0]) if row else 0

    def filter_documents(self, filters: Optional[Dict[str, Any]] = None) -> List[Document]:
        if not self._obvector.check_table_exists(self.collection_name):
            return []
        cols = f"`{self._primary_field}`, `{self._text_field}`, `{self._vector_field}`, `{self._meta_field}`"
        if not filters:
            where = "1=1"
        else:
            try:
                where = parse_filters_to_sql(self._meta_field, filters)
            except FilterError:
                raise
        sql = f"SELECT {cols} FROM `{self.collection_name}` WHERE {where} LIMIT {MAX_LIMIT_SIZE}"
        with self._obvector.engine.connect() as conn:
            res = conn.execute(text(sql)).fetchall()
        return [self._row_to_document(dict(row._mapping)) for row in res]

    def write_documents(self, documents: List[Document], policy: DuplicatePolicy = DuplicatePolicy.NONE) -> int:
        documents_cp = [deepcopy(d) for d in documents]
        documents_cp = [OceanBaseDocumentStore._discard_invalid_meta(doc) for doc in documents_cp]
        if len(documents_cp) > 0 and not isinstance(documents_cp[0], Document):
            raise ValueError("param 'documents' must contain a list of objects of type Document")

        if policy not in [DuplicatePolicy.NONE]:
            logger.warning(
                "Duplicate primary keys are enforced by the database; prefer DuplicatePolicy.NONE and unique ids."
            )

        embedding_dim = int(self._embedding_dim) if self._embedding_dim else 128
        for doc in documents_cp:
            if doc.embedding is not None:
                embedding_dim = len(doc.embedding)
                break

        empty_embedding = False
        empty_sparse = False
        for doc in documents_cp:
            if doc.embedding is None:
                empty_embedding = True
                doc.embedding = [self._dummy_value] * embedding_dim
            if self._sparse_vector_field and doc.sparse_embedding is None:
                empty_sparse = True
                doc.sparse_embedding = SparseEmbedding(indices=[0], values=[self._dummy_value])
            if doc.content is None:
                doc.content = ""

        if empty_embedding:
            logger.warning(
                "Missing dense embeddings; dummy vectors were written and may hurt retrieval quality. "
                "Compute embeddings before writing."
            )
        if empty_sparse and self._sparse_vector_field:
            logger.warning(
                "sparse_vector_field is set but documents lack sparse_embedding; dummy sparse vectors were written."
            )

        self._ensure_table(embedding_dim)

        data: List[Dict[str, Any]] = []
        for doc in documents_cp:
            row: Dict[str, Any] = {
                self._primary_field: doc.id,
                self._text_field: doc.content,
                self._vector_field: self._normalize_vec(doc.embedding) if self.normalize else doc.embedding,
                self._meta_field: doc.meta or {},
            }
            if self._sparse_vector_field:
                row[self._sparse_vector_field] = self._sparse_to_ob(doc.sparse_embedding)
            data.append(row)

        if not data:
            return 0

        batch_size = 1000
        total = 0
        for i in range(0, len(data), batch_size):
            batch = data[i : i + batch_size]
            self._obvector.upsert(table_name=self.collection_name, data=batch, partition_name="")
            total += len(batch)
        return total

    def delete_documents(self, document_ids: List[str]) -> None:
        if not document_ids:
            return
        if not self._obvector.check_table_exists(self.collection_name):
            return
        self._obvector.delete(table_name=self.collection_name, ids=document_ids)

    def to_dict(self) -> Dict[str, Any]:
        new_connection_args: Dict[str, Any] = {}
        for k, v in self.connection_args.items():
            if isinstance(v, Secret):
                new_connection_args[k] = v.to_dict()
            else:
                new_connection_args[k] = v
        init_parameters = {
            "collection_name": self.collection_name,
            "connection_args": new_connection_args,
            "drop_old": self.drop_old,
            "primary_field": self._primary_field,
            "text_field": self._text_field,
            "vector_field": self._vector_field,
            "meta_field": self._meta_field,
            "sparse_vector_field": self._sparse_vector_field,
            "index_params": self.index_params,
            "search_params": self.search_params,
            "vidx_name": self.vidx_name,
            "normalize": self.normalize,
            "embedding_dim": self._embedding_dim,
            "vidx_metric_type": self.vidx_metric_type,
            "index_type": self.index_type,
            "vidx_algo_params": self.vidx_algo_params,
        }
        return default_to_dict(self, **init_parameters)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OceanBaseDocumentStore":
        for conn_arg_key, conn_arg_value in data["init_parameters"]["connection_args"].items():
            if isinstance(conn_arg_value, dict) and conn_arg_value.get("type") == "env_var":
                deserialize_secrets_inplace(data["init_parameters"]["connection_args"], keys=[conn_arg_key])
        return default_from_dict(cls, data)

    def _normalize_vec(self, emb: List[float]) -> List[float]:
        norm = math.sqrt(sum(x * x for x in emb))
        if norm == 0:
            return emb
        return [x / norm for x in emb]

    def _sparse_to_ob(self, sp: Optional[SparseEmbedding]) -> Any:
        if sp is None:
            return None
        d = dict(zip(sp.indices, sp.values))
        return d

    def _embedding_retrieval(
        self,
        query_embedding: List[float],
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
        query_text: Optional[str] = None,
    ) -> List[Document]:
        _ = query_text
        if not self._obvector.check_table_exists(self.collection_name):
            return []

        self._handle_hnsw_ef_search()
        fltr = None
        if filters:
            fltr = parse_filters_to_sql(self._meta_field, filters)

        qv = self._normalize_vec(query_embedding) if self.normalize else query_embedding
        res = self._obvector.ann_search(
            table_name=self.collection_name,
            vec_data=qv,
            vec_column_name=self._vector_field,
            distance_func=_distance_fn(self.vidx_metric_type),
            with_dist=True,
            topk=top_k,
            output_column_names=[self._text_field, self._meta_field, self._primary_field],
            where_clause=([text(fltr)] if fltr else None),
        )
        rows = res.fetchall()
        docs: List[Document] = []
        score_fn = self._select_score_fn()
        for r in rows:
            content = r[0]
            meta_raw = r[1]
            pid = r[2]
            dist = float(r[3]) if len(r) > 3 else 0.0
            meta = json.loads(meta_raw) if isinstance(meta_raw, str) else (meta_raw or {})
            doc = Document(id=str(pid), content=content, meta=meta if isinstance(meta, dict) else {})
            doc.score = score_fn(dist)
            docs.append(doc)
        return docs

    def _sparse_embedding_retrieval(
        self,
        query_sparse_embedding: SparseEmbedding,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
        query_text: Optional[str] = None,
    ) -> List[Document]:
        _ = query_text
        if not self._sparse_vector_field:
            raise OceanBaseStoreError("Set sparse_vector_field on OceanBaseDocumentStore before sparse retrieval.")
        if not self._obvector.check_table_exists(self.collection_name):
            return []

        self._handle_hnsw_ef_search()
        fltr = None
        if filters:
            fltr = parse_filters_to_sql(self._meta_field, filters)

        qsparse = self._sparse_to_ob(query_sparse_embedding)
        res = self._obvector.ann_search(
            table_name=self.collection_name,
            vec_data=qsparse,
            vec_column_name=self._sparse_vector_field,
            distance_func=inner_product,
            with_dist=True,
            topk=top_k,
            output_column_names=[self._text_field, self._meta_field, self._primary_field],
            where_clause=([text(fltr)] if fltr else None),
        )
        rows = res.fetchall()
        docs: List[Document] = []
        for r in rows:
            content = r[0]
            meta_raw = r[1]
            pid = r[2]
            dist = float(r[3]) if len(r) > 3 else 0.0
            meta = json.loads(meta_raw) if isinstance(meta_raw, str) else (meta_raw or {})
            doc = Document(id=str(pid), content=content, meta=meta if isinstance(meta, dict) else {})
            doc.score = -dist if self.vidx_metric_type == "inner_product" else dist
            docs.append(doc)
        return docs

    def _hybrid_retrieval(
        self,
        query_embedding: List[float],
        query_sparse_embedding: Optional[SparseEmbedding] = None,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
        reranker: Any = None,
        query_text: Optional[str] = None,
    ) -> List[Document]:
        _ = reranker
        if not self._sparse_vector_field:
            raise OceanBaseStoreError("Hybrid retrieval requires sparse_vector_field to be set.")
        dense = self._embedding_retrieval(
            query_embedding=query_embedding, filters=filters, top_k=top_k, query_text=query_text
        )
        if query_sparse_embedding is None:
            return dense
        sparse = self._sparse_embedding_retrieval(
            query_sparse_embedding=query_sparse_embedding, filters=filters, top_k=top_k, query_text=query_text
        )
        return _rrf_merge([dense, sparse], top_k=top_k)

    def _select_score_fn(self) -> Callable[[float], float]:
        mt = self.vidx_metric_type.lower()

        def _map_l2_to_similarity(d: float) -> float:
            return 1.0 - d / 4.0

        def _map_ip_to_similarity(d: float) -> float:
            return (d + 1.0) / 2.0

        if mt == "l2":
            return _map_l2_to_similarity
        if mt in ("inner_product", "cosine"):
            return _map_ip_to_similarity
        return lambda x: x

    def _row_to_document(self, row: Dict[str, Any]) -> Document:
        pid = row[self._primary_field]
        content = row[self._text_field]
        vec = row.get(self._vector_field)
        meta_raw = row.get(self._meta_field)
        emb = self._parse_vector(vec)
        if emb is not None and all(x == self._dummy_value for x in emb):
            emb = None
        meta = meta_raw if isinstance(meta_raw, dict) else {}
        if isinstance(meta_raw, str):
            meta = json.loads(meta_raw)
        doc = Document(id=str(pid), content=content, embedding=emb, meta=meta)
        return doc

    def _parse_vector(self, vec: Any) -> Optional[List[float]]:
        if vec is None:
            return None
        if isinstance(vec, (bytes, memoryview)):
            import struct

            return list(struct.unpack(f"{len(vec) // 4}f", bytes(vec)))
        if isinstance(vec, list):
            return [float(x) for x in vec]
        return None

    @staticmethod
    def _discard_invalid_meta(document: Document) -> Document:
        if not isinstance(document, Document):
            raise ValueError(f"Invalid document type: {type(document)}")
        if document.meta:
            new_meta = {}
            for key, value in document.meta.items():
                try:
                    json.dumps(value)
                except TypeError:
                    logger.warning(
                        "Document %s: meta key %s is not JSON-serializable and was dropped",
                        document.id,
                        key,
                    )
                    continue
                new_meta[key] = value
            document.meta = new_meta
        return document
