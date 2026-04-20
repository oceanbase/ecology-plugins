"""Default field names and enums shared with milvus-haystack conventions."""

from enum import Enum

VECTOR_FIELD = "vector"
SPARSE_VECTOR_FIELD = "sparse"
TEXT_FIELD = "text"
PRIMARY_FIELD = "id"
META_FIELD = "meta"


class EmbeddingMode(Enum):
    """Sparse vector source (aligned with milvus-haystack naming).

    OceanBase only supports model-produced sparse vectors, not Milvus BM25 built-ins.
    """

    BUILTIN_FUNCTION = "builtin_function"
    EMBEDDING_MODEL = "embedding_model"
