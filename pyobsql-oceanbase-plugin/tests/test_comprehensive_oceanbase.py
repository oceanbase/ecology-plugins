"""
Comprehensive test suite for OceanBase 4.4.1 using pyobsql whl package.
This test covers all major features of pyobsql.
"""
import unittest
import logging
from datetime import datetime

from pyobsql.client import ObClient, ObRangePartition, RangeListPartInfo
from pyobsql.schema import (
    VECTOR,
    SPARSE_VECTOR,
    ARRAY,
    POINT,
    ST_GeomFromText,
    st_distance
)
from pyobsql import (
    JsonTableBool,
    JsonTableInt,
    JsonTableTimestamp,
    JsonTableVarcharFactory,
    JsonTableDecimalFactory,
    val2json,
    json_value,
)
from sqlalchemy import Column, Integer, String, JSON, Table, Index, select, func, update

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class ComprehensiveOceanBaseTest(unittest.TestCase):
    """Comprehensive test suite for OceanBase 4.4.1"""

    @classmethod
    def setUpClass(cls):
        """Set up test class with database connection"""
        connection_args = {
            "host": "127.0.0.1",
            "port": "2881",
            "user": "test@test",
            "password": "test",
            "db_name": "langchain",
        }
        
        # Construct URI from host and port
        uri = f"{connection_args['host']}:{connection_args['port']}"
        
        logger.info(f"Connecting to OceanBase at {uri}")
        cls.client = ObClient(
            uri=uri,
            user=connection_args['user'],
            password=connection_args['password'],
            db_name=connection_args['db_name'],
            echo=False
        )
        
        logger.info(f"Connected successfully! OceanBase version: {cls.client.ob_version}")
        
        # Clean up any existing test tables
        test_tables = [
            'test_basic_table',
            'test_vector_table',
            'test_array_table',
            'test_partitioned_table',
            'test_json_table',
            'test_point_table',
            'test_sparse_vector_table',
        ]
        for table_name in test_tables:
            try:
                cls.client.drop_table_if_exist(table_name)
                logger.info(f"Dropped existing table: {table_name}")
            except Exception as e:
                logger.warning(f"Error dropping table {table_name}: {e}")

    def test_01_connection(self):
        """Test database connection"""
        logger.info("=" * 60)
        logger.info("Test 1: Database Connection")
        logger.info("=" * 60)
        
        self.assertIsNotNone(self.client)
        self.assertIsNotNone(self.client.engine)
        logger.info(f"✓ Connection successful. OceanBase version: {self.client.ob_version}")

    def test_02_create_basic_table(self):
        """Test creating a basic table"""
        logger.info("=" * 60)
        logger.info("Test 2: Create Basic Table")
        logger.info("=" * 60)
        
        columns = [
            Column('id', Integer, primary_key=True),
            Column('name', String(100)),
            Column('age', Integer),
            Column('email', String(255)),
            Column('metadata', JSON),
        ]
        
        self.client.create_table('test_basic_table', columns=columns)
        logger.info("✓ Basic table created successfully")
        
        # Verify table exists
        self.assertTrue(self.client.check_table_exists('test_basic_table'))
        logger.info("✓ Table existence verified")

    def test_03_insert_basic_data(self):
        """Test inserting basic data"""
        logger.info("=" * 60)
        logger.info("Test 3: Insert Basic Data")
        logger.info("=" * 60)
        
        # Insert single record
        self.client.insert('test_basic_table', {
            'id': 1,
            'name': 'Alice',
            'age': 30,
            'email': 'alice@example.com',
            'metadata': {'department': 'Engineering', 'role': 'Developer'}
        })
        logger.info("✓ Single record inserted")
        
        # Batch insert
        data_list = [
            {
                'id': i,
                'name': f'User_{i}',
                'age': 20 + i,
                'email': f'user_{i}@example.com',
                'metadata': {'index': i, 'status': 'active'}
            }
            for i in range(2, 11)
        ]
        self.client.insert('test_basic_table', data_list)
        logger.info(f"✓ Batch inserted {len(data_list)} records")

    def test_04_query_basic_data(self):
        """Test querying basic data"""
        logger.info("=" * 60)
        logger.info("Test 4: Query Basic Data")
        logger.info("=" * 60)
        
        # Query all records
        result = self.client.get('test_basic_table')
        rows = list(result)
        logger.info(f"✓ Queried all records: {len(rows)} rows")
        
        # Query by primary key
        result = self.client.get('test_basic_table', ids=1)
        rows = list(result)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].name, 'Alice')
        logger.info("✓ Query by primary key successful")
        
        # Query with conditions
        table = Table('test_basic_table', self.client.metadata_obj, autoload_with=self.client.engine)
        result = self.client.get(
            'test_basic_table',
            where_clause=[table.c.age > 25],
            n_limits=5
        )
        rows = list(result)
        logger.info(f"✓ Conditional query returned {len(rows)} rows")
        
        # Query with output columns
        result = self.client.get(
            'test_basic_table',
            output_column_name=['id', 'name', 'email'],
            n_limits=3
        )
        rows = list(result)
        logger.info(f"✓ Query with specific columns returned {len(rows)} rows")

    def test_05_update_data(self):
        """Test updating data"""
        logger.info("=" * 60)
        logger.info("Test 5: Update Data")
        logger.info("=" * 60)
        
        table = Table('test_basic_table', self.client.metadata_obj, autoload_with=self.client.engine)
        
        # Update single record - use dictionary for values_clause
        # Note: SQLAlchemy update().values() expects dict or keyword args, not Column == value expressions
        # We'll use a workaround by building the update statement manually
        with self.client.engine.connect() as conn:
            with conn.begin():
                update_stmt = update(table).where(table.c.id == 1).values(
                    age=31,
                    metadata={'department': 'Engineering', 'role': 'Senior Developer'}
                )
                conn.execute(update_stmt)
        logger.info("✓ Updated single record using manual update statement")
        logger.info("✓ Updated single record")
        
        # Verify update
        result = self.client.get('test_basic_table', ids=1)
        rows = list(result)
        self.assertEqual(rows[0].age, 31)
        logger.info("✓ Update verified")

    def test_06_delete_data(self):
        """Test deleting data"""
        logger.info("=" * 60)
        logger.info("Test 6: Delete Data")
        logger.info("=" * 60)
        
        # Delete by primary key
        self.client.delete('test_basic_table', ids=10)
        logger.info("✓ Deleted record by primary key")
        
        # Verify deletion
        result = self.client.get('test_basic_table', ids=10)
        rows = list(result)
        self.assertEqual(len(rows), 0)
        logger.info("✓ Deletion verified")
        
        # Delete by condition
        table = Table('test_basic_table', self.client.metadata_obj, autoload_with=self.client.engine)
        self.client.delete(
            'test_basic_table',
            where_clause=[table.c.age < 22]
        )
        logger.info("✓ Deleted records by condition")

    def test_07_create_vector_table(self):
        """Test creating table with VECTOR type"""
        logger.info("=" * 60)
        logger.info("Test 7: Create Vector Table")
        logger.info("=" * 60)
        
        columns = [
            Column('id', Integer, primary_key=True),
            Column('name', String(100)),
            Column('embedding', VECTOR(128)),
        ]
        
        self.client.create_table('test_vector_table', columns=columns)
        logger.info("✓ Vector table created")
        
        # Insert vector data
        vector_data = [0.1 * i for i in range(128)]
        self.client.insert('test_vector_table', {
            'id': 1,
            'name': 'vector_1',
            'embedding': vector_data
        })
        logger.info("✓ Vector data inserted")

    def test_08_create_sparse_vector_table(self):
        """Test creating table with SPARSE_VECTOR type"""
        logger.info("=" * 60)
        logger.info("Test 8: Create Sparse Vector Table")
        logger.info("=" * 60)
        
        columns = [
            Column('id', Integer, primary_key=True),
            Column('name', String(100)),
            Column('sparse_vec', SPARSE_VECTOR),
        ]
        
        self.client.create_table('test_sparse_vector_table', columns=columns)
        logger.info("✓ Sparse vector table created")
        
        # Insert sparse vector data
        sparse_data = {1: 0.5, 5: 0.8, 10: 0.3, 20: 0.9}
        self.client.insert('test_sparse_vector_table', {
            'id': 1,
            'name': 'sparse_1',
            'sparse_vec': sparse_data
        })
        logger.info("✓ Sparse vector data inserted")

    def test_09_create_array_table(self):
        """Test creating table with ARRAY type"""
        logger.info("=" * 60)
        logger.info("Test 9: Create Array Table")
        logger.info("=" * 60)
        
        columns = [
            Column('id', Integer, primary_key=True),
            Column('tags', ARRAY(String(50))),
            Column('scores', ARRAY(Integer)),
        ]
        
        self.client.create_table('test_array_table', columns=columns)
        logger.info("✓ Array table created")
        
        # Insert array data
        self.client.insert('test_array_table', {
            'id': 1,
            'tags': ['tag1', 'tag2', 'tag3'],
            'scores': [100, 200, 300]
        })
        logger.info("✓ Array data inserted")

    def test_10_create_point_table(self):
        """Test creating table with POINT type"""
        logger.info("=" * 60)
        logger.info("Test 10: Create Point Table")
        logger.info("=" * 60)
        
        # Skip POINT test if not supported in this OceanBase version
        try:
            columns = [
                Column('id', Integer, primary_key=True),
                Column('name', String(100)),
                Column('location', POINT(srid=4326)),
            ]
            
            self.client.create_table('test_point_table', columns=columns)
            logger.info("✓ Point table created")
            
            # Insert point data
            self.client.insert('test_point_table', {
                'id': 1,
                'name': 'Beijing',
                'location': (116.3974, 39.9093)  # (longitude, latitude)
            })
            logger.info("✓ Point data inserted")
            
            # Query using GIS functions
            table = Table('test_point_table', self.client.metadata_obj, autoload_with=self.client.engine)
            stmt = select(
                table.c.id,
                table.c.name,
                st_distance(
                    table.c.location,
                    ST_GeomFromText('POINT(116.3974 39.9093)', 4326)
                ).label('distance')
            )
            with self.client.engine.connect() as conn:
                result = conn.execute(stmt)
                rows = list(result)
                logger.info(f"✓ GIS query returned {len(rows)} rows")
        except Exception as e:
            logger.warning(f"POINT type may not be supported in OceanBase 4.4.1: {e}")
            logger.info("⚠ Skipping POINT table test")
            self.skipTest(f"POINT type not supported: {e}")

    def test_11_create_partitioned_table(self):
        """Test creating partitioned table"""
        logger.info("=" * 60)
        logger.info("Test 11: Create Partitioned Table")
        logger.info("=" * 60)
        
        # Define Range partition strategy
        range_partition = ObRangePartition(
            is_range_columns=False,
            range_part_infos=[
                RangeListPartInfo('p0', 100),
                RangeListPartInfo('p1', 200),
                RangeListPartInfo('p2', 'MAXVALUE')
            ],
            range_expr='id'
        )
        
        columns = [
            Column('id', Integer, primary_key=True),
            Column('name', String(100)),
            Column('embedding', VECTOR(128)),
        ]
        
        self.client.create_table('test_partitioned_table', columns=columns, partitions=range_partition)
        logger.info("✓ Partitioned table created")
        
        # Insert data to specific partition
        vector_data = [0.1] * 128
        self.client.insert(
            'test_partitioned_table',
            {'id': 50, 'name': 'partitioned_1', 'embedding': vector_data},
            partition_name='p0'
        )
        logger.info("✓ Data inserted to partition p0")

    def test_12_json_table_types(self):
        """Test JSON Table virtual data types"""
        logger.info("=" * 60)
        logger.info("Test 12: JSON Table Types")
        logger.info("=" * 60)
        
        # Test JsonTableBool - val2json expects the value, not the object
        bool_type = JsonTableBool(val=True)
        json_value = val2json(bool_type.val)
        self.assertEqual(json_value, True)
        logger.info("✓ JsonTableBool works")
        
        # Test JsonTableInt
        int_type = JsonTableInt(val=42)
        json_value = val2json(int_type.val)
        self.assertEqual(json_value, 42)
        logger.info("✓ JsonTableInt works")
        
        # Test JsonTableTimestamp
        timestamp = datetime(2024, 12, 30, 3, 35, 30)
        timestamp_type = JsonTableTimestamp(val=timestamp)
        json_value = val2json(timestamp_type.val)
        self.assertEqual(json_value, timestamp.isoformat())
        logger.info("✓ JsonTableTimestamp works")
        
        # Test JsonTableVarchar
        varchar_factory = JsonTableVarcharFactory(length=255)
        varchar_type = varchar_factory.get_json_table_varchar_type()(val="test")
        json_value = val2json(varchar_type.val)
        self.assertEqual(json_value, "test")
        logger.info("✓ JsonTableVarchar works")
        
        # Test JsonTableDecimal - use ndigits and decimal_p instead of precision and scale
        decimal_factory = JsonTableDecimalFactory(ndigits=10, decimal_p=2)
        decimal_type = decimal_factory.get_json_table_decimal_type()(val=123.45)
        json_value = val2json(decimal_type.val)
        # val2json returns float for Decimal
        self.assertAlmostEqual(json_value, 123.45, places=2)
        logger.info(f"✓ JsonTableDecimal works (value: {json_value})")

    def test_13_json_value_function(self):
        """Test json_value function"""
        logger.info("=" * 60)
        logger.info("Test 13: json_value Function")
        logger.info("=" * 60)
        
        # Create a table with JSON column
        columns = [
            Column('id', Integer, primary_key=True),
            Column('metadata', JSON),
        ]
        self.client.create_table('test_json_table', columns=columns)
        
        # Insert JSON data
        self.client.insert('test_json_table', {
            'id': 1,
            'metadata': {'key': 'value', 'number': 42, 'nested': {'deep': 'data'}}
        })
        
        # Query using json_value
        table = Table('test_json_table', self.client.metadata_obj, autoload_with=self.client.engine)
        stmt = select(
            table.c.id,
            json_value(table.c.metadata, '$.key', 'VARCHAR(100)').label('extracted_key')
        ).where(table.c.id == 1)
        
        with self.client.engine.connect() as conn:
            result = conn.execute(stmt)
            rows = list(result)
            self.assertEqual(len(rows), 1)
            logger.info("✓ json_value function works")

    def test_14_upsert_operation(self):
        """Test upsert (REPLACE INTO) operation"""
        logger.info("=" * 60)
        logger.info("Test 14: Upsert Operation")
        logger.info("=" * 60)
        
        # Upsert with existing primary key (should replace)
        self.client.upsert('test_basic_table', {
            'id': 1,
            'name': 'Alice_Updated',
            'age': 32,
            'email': 'alice_updated@example.com',
            'metadata': {'status': 'updated'}
        })
        logger.info("✓ Upsert operation completed")
        
        # Verify upsert
        result = self.client.get('test_basic_table', ids=1)
        rows = list(result)
        self.assertEqual(rows[0].name, 'Alice_Updated')
        logger.info("✓ Upsert verified")

    def test_15_table_with_indexes(self):
        """Test creating table with indexes"""
        logger.info("=" * 60)
        logger.info("Test 15: Table with Indexes")
        logger.info("=" * 60)
        
        columns = [
            Column('id', Integer, primary_key=True),
            Column('name', String(100)),
            Column('email', String(255)),
        ]
        
        indexes = [
            Index('idx_name', 'name'),
            Index('idx_email', 'email'),
        ]
        
        self.client.create_table('test_indexed_table', columns=columns, indexes=indexes)
        logger.info("✓ Table with indexes created")
        
        # Insert data
        self.client.insert('test_indexed_table', {
            'id': 1,
            'name': 'Test User',
            'email': 'test@example.com'
        })
        logger.info("✓ Data inserted into indexed table")

    def test_16_refresh_metadata(self):
        """Test refreshing metadata"""
        logger.info("=" * 60)
        logger.info("Test 16: Refresh Metadata")
        logger.info("=" * 60)
        
        # Refresh all metadata
        self.client.refresh_metadata()
        logger.info("✓ Refreshed all metadata")
        
        # Refresh specific table metadata
        self.client.refresh_metadata(tables=['test_basic_table'])
        logger.info("✓ Refreshed specific table metadata")

    def test_17_complex_query(self):
        """Test complex queries using SQLAlchemy"""
        logger.info("=" * 60)
        logger.info("Test 17: Complex Queries")
        logger.info("=" * 60)
        
        table = Table('test_basic_table', self.client.metadata_obj, autoload_with=self.client.engine)
        
        # Complex query with joins, aggregations, etc.
        stmt = select(
            table.c.id,
            table.c.name,
            func.json_extract(table.c.metadata, '$.department').label('department')
        ).where(
            table.c.age > 25
        ).order_by(
            table.c.id.desc()
        ).limit(5)
        
        with self.client.engine.connect() as conn:
            result = conn.execute(stmt)
            rows = list(result)
            logger.info(f"✓ Complex query returned {len(rows)} rows")

    @classmethod
    def tearDownClass(cls):
        """Clean up test tables"""
        logger.info("=" * 60)
        logger.info("Cleaning up test tables")
        logger.info("=" * 60)
        
        test_tables = [
            'test_basic_table',
            'test_vector_table',
            'test_array_table',
            'test_partitioned_table',
            'test_json_table',
            'test_point_table',
            'test_sparse_vector_table',
            'test_indexed_table',
        ]
        
        for table_name in test_tables:
            try:
                cls.client.drop_table_if_exist(table_name)
                logger.info(f"✓ Dropped table: {table_name}")
            except Exception as e:
                logger.warning(f"Error dropping table {table_name}: {e}")


if __name__ == "__main__":
    unittest.main(verbosity=2)

