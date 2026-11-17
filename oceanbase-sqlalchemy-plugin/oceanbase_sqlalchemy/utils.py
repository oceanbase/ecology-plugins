"""
OceanBase Dialect Utility Module

Provides functionality for building secure connection strings.
"""

import urllib.parse


def build_safe_connection_string(
    username: str,
    password: str,
    host: str,
    port: str,
    service_name: str,
    dialect: str = "oceanbase+cx_oceanbase",
) -> str:
    """
    Build a secure connection string, ensuring proper parsing in SQLAlchemy 2.0

    Args:
        username: Database username
        password: Database password
        host: Database host
        port: Database port
        service_name: Service name
        dialect: Database dialect, defaults to oceanbase+cx_oracle

    Returns:
        str: Secure connection string
    """
    # URL encode special characters in username and password
    safe_username = urllib.parse.quote(username, safe="")
    safe_password = urllib.parse.quote(password, safe="")

    # Build connection string
    connection_string = (
        f"{dialect}://{safe_username}:{safe_password}@{host}:{port}/{service_name}"
    )
    return connection_string
