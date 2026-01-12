import unittest
from pyobsql import (
    JsonTableBool,
    JsonTableInt,
    JsonTableTimestamp,
    JsonTableVarcharFactory,
    JsonTableDecimalFactory,
    val2json)
import logging
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class JsonTableTest(unittest.TestCase):
    def setUp(self) -> None:
        return super().setUp()

    def test_json_table_bool(self):
        bool_type = JsonTableBool(val=True)
        json_value = val2json(bool_type)
        self.assertEqual(json_value, True)

        bool_type = JsonTableBool(val=False)
        json_value = val2json(bool_type)
        self.assertEqual(json_value, False)

    def test_json_table_int(self):
        int_type = JsonTableInt(val=42)
        json_value = val2json(int_type)
        self.assertEqual(json_value, 42)

    def test_json_table_timestamp(self):
        timestamp = datetime(2024, 12, 30, 3, 35, 30)
        timestamp_type = JsonTableTimestamp(val=timestamp)
        json_value = val2json(timestamp_type)
        self.assertEqual(json_value, timestamp.isoformat())

    def test_json_table_varchar(self):
        varchar_factory = JsonTableVarcharFactory(length=255)
        varchar_type = varchar_factory.get_json_table_varchar_type()(val="test")
        json_value = val2json(varchar_type)
        self.assertEqual(json_value, "test")

    def test_json_table_decimal(self):
        decimal_factory = JsonTableDecimalFactory(precision=10, scale=2)
        decimal_type = decimal_factory.get_json_table_decimal_type()(val=123.45)
        json_value = val2json(decimal_type)
        self.assertEqual(json_value, "123.45")


if __name__ == "__main__":
    unittest.main()

