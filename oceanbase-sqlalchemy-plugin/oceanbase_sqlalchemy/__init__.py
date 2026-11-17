"""
SQLAlchemy dialect for OceanBase Oracle mode.

This dialect extends SQLAlchemy's Oracle dialect with OceanBase-specific
optimizations and features for cx_oracle driver.
"""

# Import the cx_oracle dialect class
from .cx_oceanbase import OceanBaseDialect_cx_oceanbase
from .cx_oracle import OceanBaseDialect_cx_oracle

# Manually register the dialect for SQLAlchemy 2.0 compatibility
try:
    from sqlalchemy.dialects import registry

    registry.impls["oceanbase.cx_oracle"] = lambda: OceanBaseDialect_cx_oracle
    registry.impls["oceanbase.cx_oceanbase"] = lambda: OceanBaseDialect_cx_oceanbase
except ImportError:
    pass
