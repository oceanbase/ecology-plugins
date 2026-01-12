# pyobsql

A python SDK for OceanBase SQL, including JSON Table support and SQLAlchemy dialect extensions.

## Installation

### Install from Source

```shell
git clone https://github.com/oceanbase/ecology-plugins.git
cd ecology-plugins/pyobsql-oceanbase-plugin
pip install -e .
```

### Install from PyPI

```shell
pip install pyobsql
```

## Features

`pyobsql` provides the following features:

- **OceanBase SQL Dialect Parsing**: Extended SQLGlot support for OceanBase-specific SQL syntax
- **SQLAlchemy Integration**: Provides synchronous and asynchronous OceanBase dialect support
- **Extended Data Types**: Supports VECTOR, SPARSE_VECTOR, ARRAY, POINT and other OceanBase-specific types
- **JSON Table Support**: Virtual data types and utility functions for handling JSON tables
- **Table Structure Reflection**: Automatically parses OceanBase table structures
- **Partition Support**: Supports various partition strategies including Range, Hash, Key, List, etc.

## Detailed Usage Guide

### 1. Connect to Database

```python
from pyobsql.client import ObClient

client = ObClient(
    uri="127.0.0.1:2881",
    user="root@test",
    password="password",
    db_name="test"
)
```

### 2. Create Tables

#### 2.1 Create Basic Table

```python
from sqlalchemy import Column, Integer, String, JSON
from pyobsql.schema import VECTOR, SPARSE_VECTOR, ARRAY, POINT

columns = [
    Column('id', Integer, primary_key=True),
    Column('name', String(100)),
    Column('embedding', VECTOR(128)),
    Column('sparse_vec', SPARSE_VECTOR),
    Column('tags', ARRAY(String(50))),
    Column('location', POINT(srid=4326)),
    Column('metadata', JSON)
]

client.create_table(
    table_name='my_table',
    columns=columns
)
```

#### 2.2 Create Partitioned Table

```python
from pyobsql.client.partitions import ObRangePartition, RangeListPartInfo

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
    Column('embedding', VECTOR(128))
]

client.create_table(
    table_name='partitioned_table',
    columns=columns,
    partitions=range_partition
)
```

#### 2.3 Create Table with Indexes

```python
from sqlalchemy import Index

indexes = [
    Index('idx_name', 'name'),
    Index('idx_embedding', 'embedding', postgresql_using='hnsw')
]

client.create_table(
    table_name='indexed_table',
    columns=columns,
    indexes=indexes
)
```

### 3. Insert Data

#### 3.1 Insert Single Record

```python
client.insert(
    table_name='my_table',
    data={
        'id': 1,
        'name': 'example',
        'embedding': [0.1, 0.2, 0.3, ...],
        'sparse_vec': {1: 0.5, 5: 0.8, 10: 0.3},
        'tags': ['tag1', 'tag2', 'tag3'],
        'location': (116.3974, 39.9093),
        'metadata': {'key': 'value'}
    }
)
```

#### 3.2 Batch Insert Data

```python
data_list = [
    {
        'id': i,
        'name': f'item_{i}',
        'embedding': [0.1 * i, 0.2 * i, 0.3 * i, ...],
        'tags': [f'tag_{i}'],
        'metadata': {'index': i}
    }
    for i in range(100)
]

client.insert(
    table_name='my_table',
    data=data_list
)
```

#### 3.3 Insert to Specified Partition

```python
client.insert(
    table_name='partitioned_table',
    data={'id': 50, 'name': 'test', 'embedding': [0.1, 0.2, ...]},
    partition_name='p0'
)
```

#### 3.4 Use REPLACE INTO (Insert or Replace)

```python
from pyobsql.schema import ReplaceStmt
from sqlalchemy import Table

table = Table('my_table', client.metadata_obj, autoload_with=client.engine)
with client.engine.connect() as conn:
    with conn.begin():
        stmt = ReplaceStmt(table).values({
            'id': 1,
            'name': 'updated_name',
            'embedding': [0.5, 0.6, ...]
        })
        conn.execute(stmt)

client.upsert(
    table_name='my_table',
    data={'id': 1, 'name': 'updated_name', 'embedding': [0.5, 0.6, ...]}
)
```

### 4. Update Data

```python
from sqlalchemy import Table

table = Table('my_table', client.metadata_obj, autoload_with=client.engine)

client.update(
    table_name='my_table',
    values_clause=[table.c.name == 'new_name'],
    where_clause=[table.c.id == 1]
)

client.update(
    table_name='my_table',
    values_clause=[
        table.c.name == 'updated_name',
        table.c.metadata == {'status': 'updated'}
    ],
    where_clause=[table.c.id.in_([1, 2, 3])]
)

client.update(
    table_name='partitioned_table',
    values_clause=[table.c.name == 'new_name'],
    where_clause=[table.c.id == 50],
    partition_name='p0'
)
```

### 5. Delete Data

```python
client.delete(
    table_name='my_table',
    ids=1
)

client.delete(
    table_name='my_table',
    ids=[1, 2, 3]
)

from sqlalchemy import Table

table = Table('my_table', client.metadata_obj, autoload_with=client.engine)
client.delete(
    table_name='my_table',
    where_clause=[table.c.name == 'old_name']
)

client.delete(
    table_name='partitioned_table',
    ids=50,
    partition_name='p0'
)
```

### 6. Query Data

#### 6.1 Basic Queries

```python
from sqlalchemy import Table, select

table = Table('my_table', client.metadata_obj, autoload_with=client.engine)

result = client.get(table_name='my_table')
for row in result:
    print(row)

result = client.get(
    table_name='my_table',
    ids=1
)

result = client.get(
    table_name='my_table',
    ids=[1, 2, 3]
)

result = client.get(
    table_name='my_table',
    where_clause=[table.c.name == 'example']
)

result = client.get(
    table_name='my_table',
    output_column_name=['id', 'name', 'embedding']
)

result = client.get(
    table_name='my_table',
    n_limits=10
)

result = client.get(
    table_name='partitioned_table',
    partition_names=['p0', 'p1']
)
```

#### 6.2 Use SQLAlchemy Native Queries

```python
from sqlalchemy import Table, select, func, text

table = Table('my_table', client.metadata_obj, autoload_with=client.engine)

stmt = select(
    table.c.id,
    table.c.name,
    func.json_extract(table.c.metadata, '$.key').label('extracted_key')
).where(
    table.c.id > 10
).order_by(
    table.c.id.desc()
).limit(10)

with client.engine.connect() as conn:
    result = conn.execute(stmt)
    for row in result:
        print(row)
```

### 7. JSON Table Support

#### 7.1 JSON Table Virtual Data Types

```python
from pyobsql import (
    JsonTableBool,
    JsonTableInt,
    JsonTableTimestamp,
    JsonTableVarcharFactory,
    JsonTableDecimalFactory,
    val2json
)

bool_type = JsonTableBool(val=True)
int_type = JsonTableInt(val=42)
varchar_factory = JsonTableVarcharFactory(length=255)
varchar_type = varchar_factory.get_json_table_varchar_type()(val="test")
decimal_factory = JsonTableDecimalFactory(precision=10, scale=2)
decimal_type = decimal_factory.get_json_table_decimal_type()(val=123.45)

json_value = val2json(bool_type)
```

#### 7.2 Use json_value Function

```python
from pyobsql import json_value
from sqlalchemy import Table, select

table = Table('my_table', client.metadata_obj, autoload_with=client.engine)

stmt = select(
    table.c.id,
    json_value(table.c.metadata, '$.key', 'VARCHAR(100)').label('extracted_value')
).where(
    table.c.id == 1
)

with client.engine.connect() as conn:
    result = conn.execute(stmt)
    for row in result:
        print(row)
```

### 8. SQL Parsing (SQLGlot)

#### 8.1 Parse OceanBase SQL

```python
from pyobsql import OceanBase
from sqlglot import parse_one, transpile

sql = "ALTER TABLE t2 CHANGE COLUMN c2 changed_col INT"
ast = parse_one(sql, dialect=OceanBase)
print(ast)

sql = "ALTER TABLE t1 MODIFY COLUMN c1 VARCHAR(100) NOT NULL"
ast = parse_one(sql, dialect=OceanBase)

sql = "ALTER TABLE t1 DROP COLUMN c1"
ast = parse_one(sql, dialect=OceanBase)

sql = "SELECT * FROM table1"
mysql_sql = transpile(sql, read=OceanBase, write="mysql")[0]
```

### 9. Data Type Details

#### 9.1 VECTOR (Vector Type)

```python
from pyobsql.schema import VECTOR
from pyobsql.util import Vector

column = Column('embedding', VECTOR(128))

vector_data = [0.1, 0.2, 0.3, ...]
vector_obj = Vector(vector_data)

client.insert(
    table_name='vector_table',
    data={'id': 1, 'embedding': vector_data}
)
```

#### 9.2 SPARSE_VECTOR (Sparse Vector Type)

```python
from pyobsql.schema import SPARSE_VECTOR
from pyobsql.util import SparseVector

column = Column('sparse_vec', SPARSE_VECTOR)

sparse_data = {1: 0.5, 5: 0.8, 10: 0.3}

client.insert(
    table_name='sparse_table',
    data={'id': 1, 'sparse_vec': sparse_data}
)
```

#### 9.3 ARRAY (Array Type)

```python
from pyobsql.schema import ARRAY
from sqlalchemy import String, Integer

tags_column = Column('tags', ARRAY(String(50)))
scores_column = Column('scores', ARRAY(Integer))
nested_array = Column('matrix', ARRAY(ARRAY(Integer)))

client.insert(
    table_name='array_table',
    data={
        'id': 1,
        'tags': ['tag1', 'tag2', 'tag3'],
        'scores': [100, 200, 300],
        'matrix': [[1, 2], [3, 4]]
    }
)
```

#### 9.4 POINT (Geographic Coordinate Point Type)

```python
from pyobsql.schema import POINT

location_column = Column('location', POINT(srid=4326))

client.insert(
    table_name='location_table',
    data={
        'id': 1,
        'location': (116.3974, 39.9093)
    }
)

from pyobsql.schema import ST_GeomFromText, st_distance, st_dwithin

table = Table('location_table', client.metadata_obj, autoload_with=client.engine)
stmt = select(
    table.c.id,
    st_distance(
        table.c.location,
        ST_GeomFromText('POINT(116.3974 39.9093)', 4326)
    ).label('distance')
).where(
    st_dwithin(
        table.c.location,
        ST_GeomFromText('POINT(116.3974 39.9093)', 4326),
        1000
    )
)
```

### 10. Table Structure Management

#### 10.1 Drop Table

```python
client.drop_table_if_exist('my_table')
```

#### 10.2 Drop Index

```python
client.drop_index(table_name='my_table', index_name='idx_name')
```

#### 10.3 Refresh Metadata

```python
client.refresh_metadata()

client.refresh_metadata(tables=['my_table', 'other_table'])
```

### 11. Async Operations (Optional)

```python
from pyobsql.schema import AsyncOceanBaseDialect
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    "mysql+aiomysql://user:password@127.0.0.1:2881/dbname",
    dialect=AsyncOceanBaseDialect()
)

async with engine.connect() as conn:
    result = await conn.execute(select(table))
    rows = result.fetchall()
```

## Complete Example

```python
from pyobsql.client import ObClient
from pyobsql.client.partitions import ObRangePartition, RangeListPartInfo
from sqlalchemy import Column, Integer, String, JSON, Table
from pyobsql.schema import VECTOR, ARRAY

client = ObClient(
    uri="127.0.0.1:2881",
    user="root@test",
    password="password",
    db_name="test"
)

partition = ObRangePartition(
    is_range_columns=False,
    range_part_infos=[
        RangeListPartInfo('p0', 100),
        RangeListPartInfo('p1', 'MAXVALUE')
    ],
    range_expr='id'
)

columns = [
    Column('id', Integer, primary_key=True),
    Column('name', String(100)),
    Column('embedding', VECTOR(128)),
    Column('tags', ARRAY(String(50))),
    Column('metadata', JSON)
]

client.create_table('products', columns=columns, partitions=partition)

data = [
    {
        'id': i,
        'name': f'product_{i}',
        'embedding': [0.1 * i] * 128,
        'tags': [f'tag_{i}', f'category_{i % 5}'],
        'metadata': {'price': i * 10, 'stock': 100 - i}
    }
    for i in range(50)
]
client.insert('products', data)

table = Table('products', client.metadata_obj, autoload_with=client.engine)
result = client.get(
    table_name='products',
    where_clause=[table.c.id < 10],
    output_column_name=['id', 'name', 'tags']
)

for row in result:
    print(f"ID: {row.id}, Name: {row.name}, Tags: {row.tags}")

client.update(
    table_name='products',
    values_clause=[table.c.metadata == {'price': 999, 'stock': 50}],
    where_clause=[table.c.id == 1]
)

client.delete(table_name='products', ids=[1, 2, 3])
```

## License

Apache-2.0