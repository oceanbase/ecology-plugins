# -*- coding: utf-8 -*-
"""
OceanBase dialect for cx_oracle driver.
"""

from sqlalchemy.dialects.oracle.cx_oracle import OracleDialect_cx_oracle
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


class OceanBaseDialect_cx_oracle(OracleDialect_cx_oracle):
    """
    OceanBase dialect for cx_oracle driver.
    """

    name = "oceanbase"
    driver = "cx_oracle"

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
