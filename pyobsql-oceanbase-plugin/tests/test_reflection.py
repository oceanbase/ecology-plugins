import unittest
from pyobsql.schema import OceanBaseDialect
from sqlalchemy.dialects import registry
import logging

logger = logging.getLogger(__name__)


class ObReflectionTest(unittest.TestCase):
    def test_reflection(self):
        dialect = OceanBaseDialect()
        ddl = """CREATE TABLE `test_table` (
  `id` varchar(4096) NOT NULL,
  `text` longtext DEFAULT NULL,
  `embeddings` VECTOR(1024) DEFAULT NULL,
  `metadata` json DEFAULT NULL,
  PRIMARY KEY (`id`)
) DEFAULT CHARSET = utf8mb4 ROW_FORMAT = DYNAMIC COMPRESSION = 'zstd_1.3.8' REPLICA_NUM = 1 BLOCK_SIZE = 16384 USE_BLOOM_FILTER = FALSE TABLET_SIZE = 134217728 PCTFREE = 0
"""
        state = dialect._tabledef_parser.parse(ddl, "utf8")
        assert len(state.columns) == 4
        assert len(state.keys) == 1

    def test_dialect(self):
        uri: str = "127.0.0.1:2881"
        user: str = "root@test"
        password: str = ""
        db_name: str = "test"
        registry.register("mysql.aoceanbase", "pyobsql.schema.dialect", "AsyncOceanBaseDialect")
        connection_str = (
            f"mysql+aoceanbase://{user}:{password}@{uri}/{db_name}?charset=utf8mb4"
        )
        # Note: This does not actually create an engine, just tests registration
        # from sqlalchemy.ext.asyncio import create_async_engine
        # self.engine = create_async_engine(connection_str)


if __name__ == "__main__":
    unittest.main()

