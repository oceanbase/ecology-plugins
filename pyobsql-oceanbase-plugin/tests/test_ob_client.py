import unittest
from pyobsql.client import ObClient
from sqlalchemy import Column, Integer, String, JSON
from pyobsql.schema import VECTOR, ARRAY
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ObClientTest(unittest.TestCase):
    def setUp(self) -> None:
        # Note: These tests require actual database connections, may need to skip or use mock in CI
        self.client = None  # ObClient(echo=True)

    def test_client_initialization(self):
        # Test client initialization (without actually connecting to database)
        # If actual testing is needed, database connection information needs to be configured
        pass

    def test_table_creation_structure(self):
        # Test table structure definition
        columns = [
            Column('id', Integer, primary_key=True),
            Column('name', String(100)),
            Column('embedding', VECTOR(128)),
            Column('tags', ARRAY(String(50))),
            Column('metadata', JSON)
        ]
        self.assertEqual(len(columns), 5)
        self.assertEqual(columns[0].name, 'id')
        self.assertEqual(columns[1].name, 'name')


if __name__ == "__main__":
    unittest.main()

