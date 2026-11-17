"""
Pytest Configuration File - OceanBase Dialect Testing

This file configures the pytest environment and registers the OceanBase dialect for testing.
"""

from sqlalchemy.dialects import registry

# Register OceanBase dialect to SQLAlchemy
registry.register(
    "oceanbase.cx_oracle",
    "sqlalchemy_oceanbase.cx_oracle",
    "OceanBaseDialect_cx_oracle",
)
