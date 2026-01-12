import unittest
from pyobsql.client import (
    ObRangePartition,
    ObSubRangePartition,
    ObListPartition,
    ObSubListPartition,
    ObHashPartition,
    ObSubHashPartition,
    ObKeyPartition,
    ObSubKeyPartition,
    RangeListPartInfo,
)
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ObPartitionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None

    def test_range_and_range_columns_partition(self):
        range_part = ObRangePartition(
            False,
            range_part_infos=[
                RangeListPartInfo("p0", 100),
                RangeListPartInfo("p1", "maxvalue"),
            ],
            range_expr="id",
        )
        self.assertEqual(
            range_part.do_compile(),
            "PARTITION BY RANGE (id) (PARTITION p0 VALUES LESS THAN (100),PARTITION p1 VALUES LESS THAN (maxvalue))",
        )

        range_columns_part = ObRangePartition(
            True,
            range_part_infos=[
                RangeListPartInfo("M202001", "'2020/02/01'"),
                RangeListPartInfo("M202002", "'2020/03/01'"),
                RangeListPartInfo("M202003", "'2020/04/01'"),
                RangeListPartInfo("MMAX", "MAXVALUE"),
            ],
            col_name_list=["log_date"],
        )
        self.assertEqual(
            range_columns_part.do_compile(),
            "PARTITION BY RANGE COLUMNS (log_date) (PARTITION M202001 VALUES LESS THAN ('2020/02/01'),PARTITION M202002 VALUES LESS THAN ('2020/03/01'),PARTITION M202003 VALUES LESS THAN ('2020/04/01'),PARTITION MMAX VALUES LESS THAN (MAXVALUE))",
        )

    def test_list_and_list_columns_partition(self):
        list_part = ObListPartition(
            False,
            list_part_infos=[
                RangeListPartInfo("p0", [1, 2, 3]),
                RangeListPartInfo("p1", [5, 6]),
                RangeListPartInfo("p2", "DEFAULT"),
            ],
            list_expr="col1",
        )
        self.assertEqual(
            list_part.do_compile(),
            "PARTITION BY LIST (col1) (PARTITION p0 VALUES IN (1,2,3),PARTITION p1 VALUES IN (5,6),PARTITION p2 VALUES IN (DEFAULT))",
        )

        list_columns_part = ObListPartition(
            True,
            list_part_infos=[
                RangeListPartInfo("p0", ["'00'", "'01'"]),
                RangeListPartInfo("p1", ["'02'", "'03'"]),
                RangeListPartInfo("p2", "DEFAULT"),
            ],
            col_name_list=["partition_id"],
        )
        self.assertEqual(
            list_columns_part.do_compile(),
            "PARTITION BY LIST COLUMNS (partition_id) (PARTITION p0 VALUES IN ('00','01'),PARTITION p1 VALUES IN ('02','03'),PARTITION p2 VALUES IN (DEFAULT))",
        )

    def test_hash_and_key_partition(self):
        hash_part = ObHashPartition("col1", part_count=60)
        self.assertEqual(
            hash_part.do_compile(), "PARTITION BY HASH (col1) PARTITIONS 60"
        )

        key_part = ObKeyPartition(col_name_list=["id", "gmt_create"], part_count=10)
        self.assertEqual(
            key_part.do_compile(), "PARTITION BY KEY (id,gmt_create) PARTITIONS 10"
        )

    def test_range_columns_with_sub_partition(self):
        range_columns_part = ObRangePartition(
            True,
            range_part_infos=[
                RangeListPartInfo("p0", 100),
                RangeListPartInfo("p1", 200),
                RangeListPartInfo("p2", 300),
            ],
            col_name_list=["col1"],
        )
        range_sub_part = ObSubRangePartition(
            False,
            range_part_infos=[
                RangeListPartInfo("mp0", 1000),
                RangeListPartInfo("mp1", 2000),
                RangeListPartInfo("mp2", 3000),
            ],
            range_expr="col3",
        )
        range_columns_part.add_subpartition(range_sub_part)
        self.assertEqual(
            range_columns_part.do_compile(),
            "PARTITION BY RANGE COLUMNS (col1) SUBPARTITION BY RANGE (col3) SUBPARTITION TEMPLATE (SUBPARTITION mp0 VALUES LESS THAN (1000),SUBPARTITION mp1 VALUES LESS THAN (2000),SUBPARTITION mp2 VALUES LESS THAN (3000)) (PARTITION p0 VALUES LESS THAN (100),PARTITION p1 VALUES LESS THAN (200),PARTITION p2 VALUES LESS THAN (300))",
        )


if __name__ == "__main__":
    unittest.main()

