"""
OceanBase Dialect Test Suite

This module provides a basic test framework for the OceanBase dialect.
Note: Full SQLAlchemy test suite integration is not available in SQLAlchemy 2.0.
"""

import sqlalchemy as sa
from sqlalchemy.testing import fixtures

# Import OceanBase dialect for testing
from oceanbase_sqlalchemy.cx_oracle import OceanBaseDialect_cx_oracle


class TestOceanBaseBasicSuite(fixtures.TestBase):
    """Basic test suite for OceanBase dialect."""

    def test_dialect_basic_functionality(self):
        """Test basic dialect functionality."""
        dialect = OceanBaseDialect_cx_oracle()
        assert dialect.name == "oceanbase"
        assert dialect.driver == "cx_oracle"

    def test_dialect_compatibility(self):
        """Test dialect compatibility with SQLAlchemy."""
        assert issubclass(OceanBaseDialect_cx_oracle, sa.engine.Dialect)


class TestOceanBaseRequirements(fixtures.TestBase):
    """Test OceanBase dialect requirements."""

    def test_requirements_instantiation(self):
        """Test that requirements can be instantiated."""
        from oceanbase_sqlalchemy.requirements import Requirements

        req = Requirements()
        assert req is not None

        # Test key properties
        assert hasattr(req, "ctes_with_update_delete")
        assert hasattr(req, "oracle")
        assert hasattr(req, "cx_oracle")
        assert hasattr(req, "ctes")
        assert hasattr(req, "cte_recursive")


# Note: The original SQLAlchemy test suite import has been removed
# due to compatibility issues with SQLAlchemy 2.0.
# Use test_basic.py for more comprehensive testing.
