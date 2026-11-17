# SQLAlchemy OceanBase 方言

[![PyPI version](https://badge.fury.io/py/oceanbase-sqlalchemy.svg)](https://badge.fury.io/py/oceanbase-sqlalchemy)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/downloads/)

为 OceanBase Oracle 模式提供的 SQLAlchemy 方言，实现 SQLAlchemy 与 OceanBase 数据库的无缝集成。

## 特性

- **完全兼容**: 支持 SQLAlchemy 1.3.x 和 2.0+
- **性能优化**: 专门为 OceanBase 优化的增强 SQL 查询
- **高级反射**: 具有 OceanBase 特定优化的增强约束反射
- **连接安全**: 安全的连接字符串构建工具

## 安装

### 从 PyPI 安装（推荐）

```bash
pip install oceanbase-sqlalchemy
```

### 从源码安装

```bash
git clone https://github.com/oceanbase/ecology-plugins.git
cd ecology-plugins/oceanbase-sqlalchemy-plugin
pip install -e .
```

## 快速开始

### 基本用法

```python
from sqlalchemy import create_engine, text
from oceanbase_sqlalchemy.utils import build_safe_connection_string

# 构建连接字符串
connection_string = build_safe_connection_string(
    username="your_username",
    password="your_password",
    host="your_host",
    port="2881",
    service_name="your_service_name",
)

# 创建引擎
engine = create_engine(connection_string)

# 测试连接
with engine.connect() as conn:
    result = conn.execute(text("SELECT 1 FROM DUAL"))
    print(result.fetchone())
```

### 与 SQLAlchemy ORM 结合使用

```python
from sqlalchemy import create_engine, Column, Integer, String, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
from oceanbase_sqlalchemy.utils import build_safe_connection_string

# 创建引擎
connection_string = build_safe_connection_string(
    username="your_username",
    password="your_password",
    host="your_host",
    port="2881",
    service_name="your_service_name",
)
engine = create_engine(connection_string)

# 定义模型
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    email = Column(String(100))


# 创建表
Base.metadata.create_all(engine)
```


## 系统要求

- Python 3.7+
- SQLAlchemy 1.3.x 或 2.0+
- cx_Oracle（用于 Oracle 模式）


## 贡献

我们欢迎贡献！请查看我们的[贡献指南](CONTRIBUTING.md)了解详情。

1. Fork 仓库
2. 创建您的功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开 Pull Request


## 许可证

本项目采用 Apache License 2.0 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 支持

- **问题反馈**: [GitHub Issues](https://github.com/oceanbase/ecology-plugins/issues)
- **社区**: [OceanBase 社区](https://www.oceanbase.com/community)


## 常见问题

### Q: 如何连接到 OceanBase MySQL 模式？
A: 当前版本仅支持 OceanBase Oracle 模式。对于 MySQL 模式，请使用标准的 MySQL 驱动。

### Q: 支持哪些 SQLAlchemy 版本？
A: 支持 SQLAlchemy 1.3.x 和 2.0+ 版本。


## 故障排除

### 连接问题
- 检查网络连接和防火墙设置
- 验证用户名、密码和服务名
- 确认端口号正确（默认 2881）

### 性能问题
- 启用 SQL 日志记录 (`echo=True`) 查看执行的 SQL
- 分析慢查询日志

### 兼容性问题
- 确保使用支持的 SQLAlchemy 版本
- 检查 cx_Oracle 驱动版本
- 查看 OceanBase 版本兼容性
