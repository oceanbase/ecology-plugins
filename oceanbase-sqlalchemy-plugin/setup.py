#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="oceanbase-sqlalchemy",
    version="0.2.0",
    description="SQLAlchemy dialect for OceanBase Oracle mode (supports SQLAlchemy 1.3.x and 2.0+)",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="OceanBase Team",
    author_email="support@oceanbase.com",
    url="https://github.com/oceanbase/ecology-plugins",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    keywords="sqlalchemy oceanbase oracle dialect database",
    install_requires=[
        "sqlalchemy>=1.3.0",
        "cx_oracle>=8.0.0",
    ],
    entry_points={
        "sqlalchemy.dialects": [
            "oceanbase.cx_oracle = oceanbase_sqlalchemy.cx_oracle:OceanBaseDialect_cx_oracle",
            "oceanbase.cx_oceanbase = oceanbase_sqlalchemy.cx_oceanbase:OceanBaseDialect_cx_oceanbase",
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.7",
    project_urls={
        "Bug Reports": "https://github.com/oceanbase/ecology-plugins/issues",
        "Source": "https://github.com/oceanbase/ecology-plugins",
        "Documentation": "https://github.com/oceanbase/ecology-plugins#readme",
    },
)
