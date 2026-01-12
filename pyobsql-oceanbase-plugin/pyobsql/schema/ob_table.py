"""ObTable: extension to Table for OceanBase-specific features."""
from sqlalchemy import Table
from sqlalchemy.sql.ddl import SchemaGenerator


class ObSchemaGenerator(SchemaGenerator):
    """Schema generator for ObTable (simplified version without vector index support)."""
    pass


class ObTable(Table):
    """A class extends SQLAlchemy Table for OceanBase-specific table creation."""
    def create(self, bind, checkfirst: bool = False) -> None:
        """Create table with OceanBase-specific features.
        
        Args:
            bind: SQL engine or connection
            checkfirst: check if table exists before creating
        """
        bind._run_ddl_visitor(ObSchemaGenerator, self, checkfirst=checkfirst)




