# SQLAlchemy OceanBase Dialect

[![PyPI version](https://badge.fury.io/py/oceanbase-sqlalchemy.svg)](https://badge.fury.io/py/oceanbase-sqlalchemy)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/downloads/)

A SQLAlchemy dialect for OceanBase Oracle mode, providing seamless integration between SQLAlchemy and OceanBase database.

## Features

- **Full Compatibility**: Supports SQLAlchemy 1.3.x and 2.0+
- **Optimized Performance**: Enhanced SQL queries specifically optimized for OceanBase
- **Advanced Reflection**: Enhanced constraint reflection with OceanBase-specific optimizations
- **Connection Safety**: Secure connection string building utilities

## Installation

### From PyPI (Recommended)

```bash
pip install oceanbase-sqlalchemy
```

### From Source

```bash
git clone https://github.com/oceanbase/ecology-plugins.git
cd ecology-plugins/oceanbase-sqlalchemy-plugin
pip install -e .
```

## Quick Start

### Basic Usage

```python
from sqlalchemy import create_engine, text
from oceanbase_sqlalchemy.utils import build_safe_connection_string

# Build connection string
connection_string = build_safe_connection_string(
    username="your_username",
    password="your_password",
    host="your_host",
    port="2881",
    service_name="your_service_name",
)

# Create engine
engine = create_engine(connection_string)

# Test connection
with engine.connect() as conn:
    result = conn.execute(text("SELECT 1 FROM DUAL"))
    print(result.fetchone())
```

### Using with SQLAlchemy ORM

```python
from sqlalchemy import create_engine, Column, Integer, String, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
from oceanbase_sqlalchemy.utils import build_safe_connection_string

# Create engine
connection_string = build_safe_connection_string(
    username="your_username",
    password="your_password",
    host="your_host",
    port="2881",
    service_name="your_service_name",
)
engine = create_engine(connection_string)

# Define model
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    email = Column(String(100))


# Create tables
Base.metadata.create_all(engine)
```


## Requirements

- Python 3.7+
- SQLAlchemy 1.3.x or 2.0+
- cx_Oracle (for Oracle mode)

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request


## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/oceanbase/ecology-plugins/issues)
- **Community**: [OceanBase Community](https://www.oceanbase.com/community)


## FAQ

### Q: How to connect to OceanBase MySQL mode?
A: The current version only supports OceanBase Oracle mode. For MySQL mode, please use the standard MySQL driver.

### Q: Which SQLAlchemy versions are supported?
A: Supports SQLAlchemy 1.3.x and 2.0+ versions.


## Troubleshooting

### Connection Issues
- Check network connection and firewall settings
- Verify username, password and service name
- Confirm the port number is correct (default 2881)

### Performance Issues
- Enable SQL logging (`echo=True`) to view executed SQL
- Analyze slow query logs

### Compatibility Issues
- Ensure using supported SQLAlchemy version
- Check cx_Oracle driver version
- Review OceanBase version compatibility
