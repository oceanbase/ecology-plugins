# pyobsql Quick Start Guide

Get started with pyobsql in 5 minutes! This guide will walk you through the basics of using pyobsql to interact with OceanBase databases.

## Prerequisites

- Python 3.9 or higher
- OceanBase database (version 4.4.1 or later)
- Database connection credentials

## Installation

Install pyobsql using pip:

```bash
pip install pyobsql
```

Or install from source:

```bash
git clone https://github.com/oceanbase/pyobsql.git
cd pyobsql
pip install -e .
```

## Step 1: Connect to OceanBase

First, import and create a client connection:

```python
from pyobsql.client import ObClient

client = ObClient(
    uri="127.0.0.1:2881",      # Host:Port
    user="root@test",          # Username@Tenant
    password="your_password",   # Password
    db_name="test"             # Database name
)

print(f"Connected! OceanBase version: {client.ob_version}")
```

**Connection Parameters:**
- `uri`: Database host and port (format: `host:port`)
- `user`: Username with tenant (format: `username@tenant`)
- `password`: Database password
- `db_name`: Name of the database to connect to

## Step 2: Create Your First Table

Define table columns and create a table:

```python
from sqlalchemy import Column, Integer, String, JSON

columns = [
    Column('id', Integer, primary_key=True),
    Column('name', String(100)),
    Column('age', Integer),
    Column('email', String(255)),
    Column('metadata', JSON)
]

client.create_table('users', columns=columns)
print("Table 'users' created successfully!")
```

## Step 3: Insert Data

Insert a single record:

```python
client.insert('users', {
    'id': 1,
    'name': 'Alice',
    'age': 30,
    'email': 'alice@example.com',
    'metadata': {'department': 'Engineering', 'role': 'Developer'}
})
```

Insert multiple records at once:

```python
users_data = [
    {'id': 2, 'name': 'Bob', 'age': 25, 'email': 'bob@example.com', 'metadata': {}},
    {'id': 3, 'name': 'Charlie', 'age': 35, 'email': 'charlie@example.com', 'metadata': {}}
]

client.insert('users', users_data)
```

## Step 4: Query Data

Query all records:

```python
result = client.get('users')
for row in result:
    print(f"ID: {row.id}, Name: {row.name}, Email: {row.email}")
```

Query by primary key:

```python
result = client.get('users', ids=1)
user = list(result)[0]
print(f"Found user: {user.name}")
```

Query with conditions:

```python
from sqlalchemy import Table

table = Table('users', client.metadata_obj, autoload_with=client.engine)

# Find users older than 25
result = client.get(
    'users',
    where_clause=[table.c.age > 25],
    n_limits=10
)

for row in result:
    print(f"{row.name} is {row.age} years old")
```

## Step 5: Update Data

Update records using SQLAlchemy:

```python
from sqlalchemy import Table, update

table = Table('users', client.metadata_obj, autoload_with=client.engine)

with client.engine.connect() as conn:
    with conn.begin():
        update_stmt = update(table).where(table.c.id == 1).values(
            age=31,
            metadata={'department': 'Engineering', 'role': 'Senior Developer'}
        )
        conn.execute(update_stmt)

print("User updated successfully!")
```

## Step 6: Delete Data

Delete by primary key:

```python
client.delete('users', ids=1)
```

Delete multiple records:

```python
client.delete('users', ids=[2, 3])
```

Delete with conditions:

```python
table = Table('users', client.metadata_obj, autoload_with=client.engine)
client.delete('users', where_clause=[table.c.age < 18])
```

## Working with Advanced Data Types

### VECTOR Type (for embeddings)

```python
from sqlalchemy import Column, Integer, String
from pyobsql.schema import VECTOR

columns = [
    Column('id', Integer, primary_key=True),
    Column('text', String(500)),
    Column('embedding', VECTOR(128))  # 128-dimensional vector
]

client.create_table('documents', columns=columns)

# Insert vector data
embedding = [0.1] * 128  # Your embedding vector
client.insert('documents', {
    'id': 1,
    'text': 'Sample document',
    'embedding': embedding
})
```

### ARRAY Type

```python
from pyobsql.schema import ARRAY

columns = [
    Column('id', Integer, primary_key=True),
    Column('tags', ARRAY(String(50))),      # String array
    Column('scores', ARRAY(Integer))        # Integer array
]

client.create_table('items', columns=columns)

client.insert('items', {
    'id': 1,
    'tags': ['python', 'database', 'oceanbase'],
    'scores': [95, 87, 92]
})
```

### SPARSE_VECTOR Type

```python
from pyobsql.schema import SPARSE_VECTOR

columns = [
    Column('id', Integer, primary_key=True),
    Column('sparse_vec', SPARSE_VECTOR)
]

client.create_table('sparse_data', columns=columns)

# Sparse vector as dictionary: {index: value}
sparse_vector = {1: 0.5, 5: 0.8, 10: 0.3}
client.insert('sparse_data', {
    'id': 1,
    'sparse_vec': sparse_vector
})
```

### JSON Type

```python
from sqlalchemy import JSON

columns = [
    Column('id', Integer, primary_key=True),
    Column('metadata', JSON)
]

client.create_table('products', columns=columns)

client.insert('products', {
    'id': 1,
    'metadata': {
        'price': 99.99,
        'category': 'Electronics',
        'specs': {'color': 'black', 'weight': '1.5kg'}
    }
})
```

## Working with JSON Table

pyobsql provides special data types for JSON Table operations:

```python
from pyobsql import (
    JsonTableBool,
    JsonTableInt,
    JsonTableTimestamp,
    JsonTableVarcharFactory,
    JsonTableDecimalFactory,
    val2json
)

# Create JSON Table types
bool_type = JsonTableBool(val=True)
int_type = JsonTableInt(val=42)
varchar_factory = JsonTableVarcharFactory(length=255)
varchar_type = varchar_factory.get_json_table_varchar_type()(val="test")

# Convert to JSON
json_value = val2json(bool_type.val)
```

## Using json_value Function

Extract values from JSON columns:

```python
from pyobsql import json_value
from sqlalchemy import Table, select

table = Table('products', client.metadata_obj, autoload_with=client.engine)

stmt = select(
    table.c.id,
    json_value(table.c.metadata, '$.price', 'DECIMAL(10,2)').label('price')
).where(table.c.id == 1)

with client.engine.connect() as conn:
    result = conn.execute(stmt)
    for row in result:
        print(f"Product {row.id} price: {row.price}")
```

## Creating Partitioned Tables

Create a table with Range partitioning:

```python
from pyobsql.client.partitions import ObRangePartition, RangeListPartInfo

partition = ObRangePartition(
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
    Column('data', String(500))
]

client.create_table('partitioned_data', columns=columns, partitions=partition)

# Insert to specific partition
client.insert(
    'partitioned_data',
    {'id': 50, 'name': 'test', 'data': 'sample'},
    partition_name='p0'
)
```

## Upsert Operations (Insert or Replace)

Use `upsert` to insert or replace records:

```python
# If id=1 exists, replace it; otherwise insert
client.upsert('users', {
    'id': 1,
    'name': 'Alice Updated',
    'age': 31,
    'email': 'alice.new@example.com',
    'metadata': {'status': 'updated'}
})
```

## Using SQLAlchemy Queries

For complex queries, use SQLAlchemy directly:

```python
from sqlalchemy import Table, select, func

table = Table('users', client.metadata_obj, autoload_with=client.engine)

stmt = select(
    table.c.id,
    table.c.name,
    func.json_extract(table.c.metadata, '$.department').label('department')
).where(
    table.c.age > 25
).order_by(
    table.c.id.desc()
).limit(10)

with client.engine.connect() as conn:
    result = conn.execute(stmt)
    for row in result:
        print(f"{row.name} - {row.department}")
```

## Complete Example

Here's a complete working example:

```python
from pyobsql.client import ObClient
from sqlalchemy import Column, Integer, String, JSON

# 1. Connect
client = ObClient(
    uri="127.0.0.1:2881",
    user="root@test",
    password="password",
    db_name="test"
)

# 2. Create table
columns = [
    Column('id', Integer, primary_key=True),
    Column('name', String(100)),
    Column('email', String(255)),
    Column('metadata', JSON)
]
client.create_table('employees', columns=columns)

# 3. Insert data
client.insert('employees', {
    'id': 1,
    'name': 'John Doe',
    'email': 'john@example.com',
    'metadata': {'department': 'Sales', 'level': 'Senior'}
})

# 4. Query data
result = client.get('employees', ids=1)
employee = list(result)[0]
print(f"Employee: {employee.name}, Email: {employee.email}")

# 5. Update data
from sqlalchemy import Table, update
table = Table('employees', client.metadata_obj, autoload_with=client.engine)
with client.engine.connect() as conn:
    with conn.begin():
        update_stmt = update(table).where(table.c.id == 1).values(
            metadata={'department': 'Sales', 'level': 'Manager'}
        )
        conn.execute(update_stmt)

# 6. Clean up (optional)
client.drop_table_if_exist('employees')
```

## Common Operations Reference

### Check if table exists
```python
if client.check_table_exists('users'):
    print("Table exists!")
```

### Drop table
```python
client.drop_table_if_exist('users')
```

### Refresh metadata
```python
# Refresh all tables
client.refresh_metadata()

# Refresh specific tables
client.refresh_metadata(tables=['users', 'products'])
```

### Create indexes
```python
from sqlalchemy import Index

indexes = [
    Index('idx_name', 'name'),
    Index('idx_email', 'email')
]

client.create_table('users', columns=columns, indexes=indexes)
```

## Next Steps

- Read the [full README](README.md) for detailed documentation
- Explore advanced features like partitioning and vector search
- Check out the [test examples](tests/) for more use cases
- Join the community for support and updates

## Troubleshooting

### Connection Issues
- Verify your database is running and accessible
- Check firewall settings
- Ensure credentials are correct (username@tenant format)

### Import Errors
- Make sure pyobsql is installed: `pip list | grep pyobsql`
- Check Python version: `python --version` (requires 3.9+)

### Type Errors
- Ensure you're using the correct data types from `pyobsql.schema`
- Check OceanBase version compatibility (some features require 4.4.1+)

## Need Help?

- **Documentation**: See [README.md](README.md)
- **Issues**: Report on [GitHub Issues](https://github.com/oceanbase/pyobsql/issues)
- **Examples**: Check the `tests/` directory for more examples

---

**Happy coding with pyobsql! 🚀**

