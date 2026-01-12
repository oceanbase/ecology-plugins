"""A python SDK for OceanBase SQL, including JSON Table support and SQLAlchemy dialect.

`pyobsql` provides:
* OceanBase SQL dialect for SQLAlchemy
* JSON Table support with virtual data types
* SQL parsing and execution utilities
"""
from .json_table import (
    OceanBase,
    ChangeColumn,
    JType,
    JsonTableDataType,
    JsonTableBool,
    JsonTableTimestamp,
    JsonTableVarcharFactory,
    JsonTableDecimalFactory,
    JsonTableInt,
    val2json,
    json_value
)

__all__ = [
    "OceanBase",
    "ChangeColumn",
    "JType",
    "JsonTableDataType",
    "JsonTableBool",
    "JsonTableTimestamp",
    "JsonTableVarcharFactory",
    "JsonTableDecimalFactory",
    "JsonTableInt",
    "val2json",
    "json_value",
]

__version__ = "0.1.0"
