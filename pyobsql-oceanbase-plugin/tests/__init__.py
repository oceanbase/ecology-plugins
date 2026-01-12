import unittest
from pyobsql.client import ObClient
from pyobsql import OceanBase
from sqlalchemy import Column, Integer, Table
from sqlalchemy.sql import func
from sqlalchemy.exc import NoSuchTableError


class ObClientTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = ObClient(echo=True)


if __name__ == "__main__":
    unittest.main()

