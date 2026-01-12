"""A extension for SQLAlchemy for OceanBase SQL schema definition.

* ARRAY             An extended data type in SQLAlchemy
* VECTOR            An extended data type in SQLAlchemy for vector storage
* SPARSE_VECTOR     An extended data type in SQLAlchemy for sparse vector storage
* POINT             GIS Point data type
* ObTable           Extension to Table for creating table
* ReplaceStmt       Replace into statement
* FtsIndex          Full Text Search Index
* CreateFtsIndex    Full Text Search Index Creation statement clause
* MatchAgainst      Full Text Search clause
* ST_GeomFromText   GIS function: parse text to geometry object
* st_distance       GIS function: calculate distance between Points
* st_dwithin        GIS function: check if the distance between two points
* st_astext         GIS function: return a Point in human-readable format
* OceanBaseDialect  OceanBase SQLAlchemy dialect
* AsyncOceanBaseDialect  OceanBase async SQLAlchemy dialect
"""
from .array import ARRAY
from .vector import VECTOR
from .sparse_vector import SPARSE_VECTOR
from .geo_srid_point import POINT
from .ob_table import ObTable
from .replace_stmt import ReplaceStmt
from .dialect import OceanBaseDialect, AsyncOceanBaseDialect
from .full_text_index import FtsIndex, CreateFtsIndex
from .match_against_func import MatchAgainst
from .gis_func import ST_GeomFromText, st_distance, st_dwithin, st_astext

__all__ = [
    "ARRAY",
    "VECTOR",
    "SPARSE_VECTOR",
    "POINT",
    "ObTable",
    "ReplaceStmt",
    "FtsIndex",
    "CreateFtsIndex",
    "MatchAgainst",
    "ST_GeomFromText",
    "st_distance",
    "st_dwithin",
    "st_astext",
    "OceanBaseDialect",
    "AsyncOceanBaseDialect",
]




