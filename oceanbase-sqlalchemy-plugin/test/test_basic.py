"""
Basic tests for OceanBase SQLAlchemy dialect
"""

import pytest
import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.testing import fixtures

from oceanbase_sqlalchemy.cx_oracle import OceanBaseDialect_cx_oracle


class TestOceanBaseDialect(fixtures.TestBase):
    """Test basic OceanBase dialect functionality."""

    def test_dialect_import(self):
        """Test that the dialect can be imported."""
        assert OceanBaseDialect_cx_oracle is not None
        assert issubclass(OceanBaseDialect_cx_oracle, sa.engine.Dialect)

    def test_dialect_name(self):
        """Test dialect name."""
        dialect = OceanBaseDialect_cx_oracle()
        assert dialect.name == "oceanbase"

    def test_driver_name(self):
        """Test driver name."""
        dialect = OceanBaseDialect_cx_oracle()
        assert dialect.driver == "cx_oracle"

    def test_connection_string_building(self):
        """Test connection string building."""
        from oceanbase_sqlalchemy.utils import build_safe_connection_string

        conn_str = build_safe_connection_string(
            username="test_user",
            password="test_pass",
            host="localhost",
            port="2881",
            service_name="test_service",
        )

        assert "oceanbase+cx_oceanbase://" in conn_str
        assert "test_user:test_pass@localhost:2881" in conn_str
        assert "test_service" in conn_str

    def test_engine_creation(self):
        """Test engine creation with OceanBase dialect."""
        # Skip missing drivers or dialects; unexpected implementation errors
        # must fail the test instead of being mistaken for an unavailable DB.
        try:
            engine = create_engine(
                "oceanbase+cx_oracle://test:test@localhost:2881/?service_name=test"
            )
            assert engine.dialect.name == "oceanbase"
        except (ImportError, sa.exc.NoSuchModuleError) as e:
            pytest.skip(f"OceanBase not available: {e}")

    def test_sql_generation(self):
        """Test basic SQL generation."""
        # Test table creation
        table = sa.Table(
            "test_table",
            sa.MetaData(),
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(50)),
        )

        # This should not raise an exception
        create_stmt = sa.schema.CreateTable(table)
        assert create_stmt is not None


class TestOceanBaseRequirements(fixtures.TestBase):
    """Test OceanBase dialect requirements."""

    def test_requirements_class(self):
        """Test that requirements class can be instantiated."""
        from oceanbase_sqlalchemy.requirements import Requirements

        req = Requirements()
        assert req is not None

        # Test some basic properties
        assert hasattr(req, "ctes_with_update_delete")
        assert hasattr(req, "oracle")
        assert hasattr(req, "cx_oracle")


if __name__ == "__main__":
    pytest.main([__file__])
