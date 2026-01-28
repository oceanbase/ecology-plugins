# -*- coding: utf-8 -*-
"""
OceanBase dialect for cx_oracle driver.
"""

from sqlalchemy.dialects.oracle.cx_oracle import (
    OracleDialect_cx_oracle,
    OracleCompiler_cx_oracle,
)
from sqlalchemy.dialects.oracle.base import OracleCompiler
from sqlalchemy import select, and_, or_, bindparam, sql
from functools import lru_cache
from sqlalchemy.engine import reflection
import urllib.parse

# SQLAlchemy version compatibility
import sqlalchemy

SA_VERSION = sqlalchemy.__version__
SA_20_PLUS = SA_VERSION.startswith("2.")

if SA_20_PLUS:
    from sqlalchemy.dialects.oracle import dictionary


class OceanBaseCompiler_cx_oracle(OracleCompiler_cx_oracle):
    """
    Custom compiler for OceanBase to handle bind parameter naming.

    OceanBase does not support quoted bind parameter names (e.g., :"start")
    like Oracle does. This compiler disables bind parameter quoting and
    normalizes numeric-leading parameter names to match SQLAlchemy 2.0 behavior.
    """

    def bindparam_string(self, name, **kw):
        """
        Override bindparam_string to disable quoting and normalize parameter names.

        Issues:
        1. SQLAlchemy's Oracle dialect quotes bind parameter names that are
           reserved words (e.g., :start becomes :"start"). Oracle supports this,
           but OceanBase raises OBE-01036: illegal variable name/number.
        2. SQLAlchemy 1.3 doesn't handle numeric-leading parameter names
           (e.g., :123start), but SQLAlchemy 2.0+ does (converts to :D123start).

        Solution:
        1. Skip the quoting branch entirely (don't quote reserved words)
        2. Normalize parameter names that start with digits or underscores
           by prefixing with "D" (following SQLAlchemy 2.0 convention)
        """
        # Step 1: Normalize parameter names (handle numeric/underscore prefixes)
        # Only for SQLAlchemy 2.x, as 1.3 doesn't handle this and will cause errors
        if SA_20_PLUS:
            escaped_from = kw.get("escaped_from", None)
            if not escaped_from:
                if name and (name[0].isdigit() or name[0] == "_"):
                    new_name = "D" + name
                    kw["escaped_from"] = name
                    name = new_name

        return OracleCompiler.bindparam_string(self, name, **kw)


class OceanBaseDialect_cx_oracle(OracleDialect_cx_oracle):
    """
    OceanBase dialect for cx_oracle driver.
    """

    name = "oceanbase"
    driver = "cx_oracle"

    # Use custom compiler that doesn't quote bind parameter names
    statement_compiler = OceanBaseCompiler_cx_oracle

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def _supports_except_all(self):
        return False

    def create_connect_args(self, url):
        if SA_20_PLUS:
            username = url.username
            password = url.password

            if username and "%" in username:
                username = urllib.parse.unquote(username)
            if password and "%" in password:
                password = urllib.parse.unquote(password)

            if username or password:
                from sqlalchemy.engine import make_url

                new_url = make_url(str(url))
                if username:
                    new_url = new_url.set(username=username)
                if password:
                    new_url = new_url.set(password=password)
                url = new_url

        return super().create_connect_args(url)

    def _get_server_version_info(self, connection):
        """
        Get OceanBase server version information

        Issue1: cx_Oceanbase driver returns "0.0.0.0.1" for connection.version,
        causing SQLAlchemy to misidentify it as Oracle 8 and set supports_unicode_binds to False,
        which encodes all string parameters as bytes, resulting in NVARCHAR2 query failures.

        Issue2: Hard-code a pre-12c version so SQLAlchemy will not try to query
        Oracle-only dictionary views such as ALL_TAB_IDENTITY_COLS, which
        OceanBase does not implement. Unicode bind support is forced on in
        initialize(), so we do not rely on the reported version for that.
        _column_query() in base.py will fail with ORA-00942: table or view does not exist.
        """

        return (11, 2, 0, 0)

    def initialize(self, connection):
        """
        Initialize dialect to ensure OceanBase uses Unicode string binding

        OceanBase is compatible with Oracle 10g+, supporting Unicode binding.
        Even if the version number might be misjudged, force enable supports_unicode_binds.
        """
        # Call parent class initialization
        super().initialize(connection)

        # Force enable Unicode binding support
        # OceanBase fully supports Unicode and should not use bytes encoding
        self.supports_unicode_binds = True

    @reflection.cache
    def _get_constraint_data(
        self, connection, table_name, schema=None, dblink="", **kw
    ):
        params = {"table_name": table_name}

        text = (
            "SELECT /*+opt_param('XSOLAPI_GENERATE_WITH_CLAUSE','false') */"
            "\nac.constraint_name,"
            "\nac.constraint_type,"
            "\nloc.column_name AS local_column,"
            "\nrem.table_name AS remote_table,"
            "\nrem.column_name AS remote_column,"
            "\nrem.owner AS remote_owner,"
            "\nloc.position as loc_pos,"
            "\nrem.position as rem_pos,"
            "\nac.search_condition,"
            "\nac.delete_rule"
            "\nFROM all_cons_columns loc,"
            "\nall_constraints ac"
            "\nLEFT JOIN all_cons_columns rem"
            "\nON ac.r_owner = rem.owner"
            "\nAND ac.r_constraint_name = rem.constraint_name"
            "\nAND rem.table_name = :table_name"
            "\nWHERE ac.table_name = :table_name"
            "\nAND loc.table_name = :table_name"
            "\nAND ac.constraint_type IN ('R','P', 'U', 'C')"
        )

        if schema is not None:
            params["owner"] = schema
            text += "\nAND ac.owner = :owner"

        text += (
            "\nAND ac.owner = loc.owner"
            "\nAND ac.constraint_name = loc.constraint_name"
            "\nAND (rem.position IS NULL or loc.position=rem.position)"
            "\nORDER BY ac.constraint_name, loc.position"
        )

        text = text % {"dblink": dblink}
        rp = connection.execute(sql.text(text), **params)
        constraint_data = rp.fetchall()
        return constraint_data

    @lru_cache()
    def _constraint_query(self, owner):
        local = dictionary.all_cons_columns.alias("local")
        remote = dictionary.all_cons_columns.alias("remote")
        table_names = bindparam("all_objects")

        return (
            select(
                dictionary.all_constraints.c.table_name,
                dictionary.all_constraints.c.constraint_type,
                dictionary.all_constraints.c.constraint_name,
                local.c.column_name.label("local_column"),
                remote.c.table_name.label("remote_table"),
                remote.c.column_name.label("remote_column"),
                remote.c.owner.label("remote_owner"),
                dictionary.all_constraints.c.search_condition,
                dictionary.all_constraints.c.delete_rule,
            )
            .select_from(dictionary.all_constraints)
            .join(
                local,
                and_(
                    local.c.owner == dictionary.all_constraints.c.owner,
                    dictionary.all_constraints.c.constraint_name
                    == local.c.constraint_name,
                    local.c.table_name.in_(table_names),
                ),
            )
            .outerjoin(
                remote,
                and_(
                    dictionary.all_constraints.c.r_owner == remote.c.owner,
                    dictionary.all_constraints.c.r_constraint_name
                    == remote.c.constraint_name,
                    remote.c.table_name.in_(table_names),
                    or_(
                        remote.c.position.is_(sql.null()),
                        local.c.position == remote.c.position,
                    ),
                ),
            )
            .where(
                dictionary.all_constraints.c.table_name.in_(table_names),
                dictionary.all_constraints.c.owner == owner,
                dictionary.all_constraints.c.constraint_type.in_(("R", "P", "U", "C")),
            )
            .order_by(
                dictionary.all_constraints.c.constraint_name,
                local.c.position,
            )
        )

    @lru_cache()
    def _index_query(self, owner):
        """
        Override _index_query to optimize performance in OceanBase Oracle mode.

        Key optimization: Add filtering on all_ind_columns.table_name to reduce
        the amount of data scanned early in the query execution.

        Only for sqlalchemy 2.x compatibility.
        """
        return (
            select(
                dictionary.all_ind_columns.c.table_name,
                dictionary.all_ind_columns.c.index_name,
                dictionary.all_ind_columns.c.column_name,
                dictionary.all_indexes.c.index_type,
                dictionary.all_indexes.c.uniqueness,
                dictionary.all_indexes.c.compression,
                dictionary.all_indexes.c.prefix_length,
                dictionary.all_ind_columns.c.descend,
                dictionary.all_ind_expressions.c.column_expression,
            )
            .select_from(dictionary.all_ind_columns)
            .join(
                dictionary.all_indexes,
                and_(
                    dictionary.all_ind_columns.c.index_name
                    == dictionary.all_indexes.c.index_name,
                    dictionary.all_ind_columns.c.index_owner
                    == dictionary.all_indexes.c.owner,
                ),
            )
            .outerjoin(
                dictionary.all_ind_expressions,
                and_(
                    dictionary.all_ind_expressions.c.index_name
                    == dictionary.all_ind_columns.c.index_name,
                    dictionary.all_ind_expressions.c.index_owner
                    == dictionary.all_ind_columns.c.index_owner,
                    dictionary.all_ind_expressions.c.column_position
                    == dictionary.all_ind_columns.c.column_position,
                ),
            )
            .where(
                dictionary.all_indexes.c.table_owner == owner,
                dictionary.all_indexes.c.table_name.in_(bindparam("all_objects")),
                # Key optimization: add this condition to reduce all_ind_columns scan
                dictionary.all_ind_columns.c.table_name.in_(bindparam("all_objects")),
            )
            .order_by(
                dictionary.all_ind_columns.c.index_name,
                dictionary.all_ind_columns.c.column_position,
            )
        )


# Register dialect, similar to SQLAlchemy's cx_oracle.py
dialect = OceanBaseDialect_cx_oracle
