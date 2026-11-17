"""
OceanBase Dialect Requirements

This file defines the capabilities and requirements for the OceanBase dialect,
which extends SQLAlchemy's Oracle dialect with OceanBase-specific optimizations.
"""

from sqlalchemy.testing import exclusions
from sqlalchemy.testing.requirements import SuiteRequirements


class Requirements(SuiteRequirements):
    """
    OceanBase Oracle mode dialect requirements.

    This class defines what features are supported or not supported
    by the OceanBase Oracle mode dialect.
    """

    @property
    def ctes_with_update_delete(self):
        """
        OceanBase supports CTEs with UPDATE/DELETE.
        """
        return exclusions.open()

    @property
    def except_all(self):
        """
        OceanBase does not support EXCEPT ALL syntax.
        This causes OBE-00900: invalid SQL statement error.
        """
        return exclusions.closed()

    @property
    def intersect_all(self):
        """
        OceanBase may not support INTERSECT ALL syntax.
        """
        return exclusions.closed()

    @property
    def union_all(self):
        """
        OceanBase supports UNION ALL syntax.
        """
        return exclusions.open()

    @property
    def returning(self):
        """
        OceanBase supports RETURNING clause.
        """
        return exclusions.open()

    @property
    def autoincrement_without_sequence(self):
        """
        OceanBase requires sequences for auto-increment columns.
        """
        return exclusions.closed()

    @property
    def sequences(self):
        """
        OceanBase supports sequences.
        """
        return exclusions.open()

    @property
    def schemas(self):
        """
        OceanBase supports schemas.
        """
        return exclusions.open()

    @property
    def cross_schema_fk_reflection(self):
        """
        OceanBase supports cross-schema foreign key reflection.
        """
        return exclusions.open()

    @property
    def foreign_key_constraint_reflection(self):
        """
        OceanBase supports foreign key constraint reflection.
        """
        return exclusions.open()

    @property
    def primary_key_constraint_reflection(self):
        """
        OceanBase supports primary key constraint reflection.
        """
        return exclusions.open()

    @property
    def unique_constraint_reflection(self):
        """
        OceanBase supports unique constraint reflection.
        """
        return exclusions.open()

    @property
    def check_constraint_reflection(self):
        """
        OceanBase supports check constraint reflection.
        """
        return exclusions.open()

    @property
    def index_reflection(self):
        """
        OceanBase supports index reflection.
        """
        return exclusions.open()

    @property
    def view_reflection(self):
        """
        OceanBase supports view reflection.
        """
        return exclusions.open()

    @property
    def temp_table_reflection(self):
        """
        OceanBase supports temporary table reflection.
        """
        return exclusions.open()

    @property
    def table_reflection(self):
        """
        OceanBase supports table reflection.
        """
        return exclusions.open()

    @property
    def column_reflection(self):
        """
        OceanBase supports column reflection.
        """
        return exclusions.open()

    @property
    def oracle(self):
        """
        OceanBase is Oracle-compatible.
        """
        return exclusions.open()

    @property
    def cx_oracle(self):
        """
        OceanBase dialect supports cx_oracle driver.
        """
        return exclusions.open()

    @property
    def ctes(self):
        """
        OceanBase supports Common Table Expressions (CTEs).
        """
        return exclusions.open()

    @property
    def cte_recursive(self):
        """
        OceanBase supports recursive CTEs.
        """
        return exclusions.open()

    @property
    def cte_works_with_dml(self):
        """
        OceanBase supports CTEs with DML statements.
        """
        return exclusions.open()

    @property
    def cte_works_with_subqueries(self):
        """
        OceanBase supports CTEs with subqueries.
        """
        return exclusions.open()

    @property
    def cte_works_with_aggregates(self):
        """
        OceanBase supports CTEs with aggregate functions.
        """
        return exclusions.open()

    @property
    def cte_works_with_window_functions(self):
        """
        OceanBase supports CTEs with window functions.
        """
        return exclusions.open()
