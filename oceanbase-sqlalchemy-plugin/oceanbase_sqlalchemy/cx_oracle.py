"""
OceanBase dialect for cx_oracle driver.
"""

import urllib.parse
from functools import lru_cache

# SQLAlchemy version compatibility
import sqlalchemy
from sqlalchemy import and_, bindparam, or_, select, sql
from sqlalchemy.dialects.oracle.base import OracleCompiler
from sqlalchemy.dialects.oracle.cx_oracle import (
    OracleCompiler_cx_oracle,
    OracleDialect_cx_oracle,
)
from sqlalchemy.engine import reflection

SA_VERSION = sqlalchemy.__version__
SA_20_PLUS = SA_VERSION.startswith("2.")

if SA_20_PLUS:
    from sqlalchemy.dialects.oracle import dictionary
    from sqlalchemy.engine.reflection import ObjectKind, ObjectScope

    _dictionary_has_ind_expressions = (
        getattr(dictionary, "all_ind_expressions", None) is not None
    )
else:
    _dictionary_has_ind_expressions = False


class OceanBaseCompiler_cx_oracle(OracleCompiler_cx_oracle):
    """
    Custom compiler for OceanBase to handle bind parameter naming.

    Keep ASCII bind names, including reserved words, unquoted for OceanBase.
    Preserve Oracle's Unicode quoting and parameter-key mapping for drivers
    that require quoted non-ASCII bind names.
    """

    def bindparam_string(self, name, **kw):
        """
        Restore Oracle's non-ASCII bind handling without changing ASCII binds.

        Delegating keeps quoted SQL placeholders and DBAPI parameter keys in
        sync on both SQLAlchemy 1.3 and 2.x. ASCII names retain the reserved-word
        fix and the existing version-specific prefix normalization.
        """
        if not name.isascii():
            return super().bindparam_string(name, **kw)

        if SA_20_PLUS:
            escaped_from = kw.get("escaped_from", None)
            if not escaped_from and name and (name[0].isdigit() or name[0] == "_"):
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

    # Keep ASCII bind names unquoted while preserving Unicode bind compatibility
    statement_compiler = OceanBaseCompiler_cx_oracle

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Keep bounded query caches on the dialect instance so discarded
        # engines/dialects are not retained by a class-level method cache.
        self._constraint_query = lru_cache(maxsize=128)(self._constraint_query)
        self._index_query = lru_cache(maxsize=128)(self._index_query)

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

    @reflection.cache
    def get_pk_constraint(self, connection, table_name, schema=None, **kw):
        """Reflect a local object's primary key in one dictionary query."""
        if not SA_20_PLUS or kw.get("oracle_resolve_synonyms") or kw.get("dblink"):
            return super().get_pk_constraint(
                connection, table_name, schema=schema, **kw
            )

        owner = self.denormalize_schema_name(schema or self.default_schema_name)
        objects = self._all_objects_query(
            owner, ObjectScope.ANY, ObjectKind.ANY, True, False
        ).subquery()
        constraints = dictionary.all_constraints.c
        columns = dictionary.all_cons_columns.c
        query = (
            select(
                objects.c.object_name, constraints.constraint_name, columns.column_name
            )
            .select_from(objects)
            .outerjoin(
                dictionary.all_constraints,
                and_(
                    constraints.owner == owner,
                    constraints.table_name == objects.c.object_name,
                    constraints.constraint_type == "P",
                ),
            )
            .outerjoin(
                dictionary.all_cons_columns,
                and_(
                    columns.owner == constraints.owner,
                    columns.table_name == constraints.table_name,
                    columns.constraint_name == constraints.constraint_name,
                ),
            )
            .order_by(columns.position)
        )
        rows = self._execute_reflection(
            connection,
            query,
            dblink=None,
            returns_long=False,
            params={"filter_names": [self.denormalize_name(table_name)]},
        ).all()
        data = {}
        if rows:
            object_name, constraint_name, _ = rows[0]
            column_names = [
                self.normalize_name(column_name)
                for _, _, column_name in rows
                if column_name is not None
            ]
            data[(schema, self.normalize_name(object_name))] = {
                "name": self.normalize_name(constraint_name) if column_names else None,
                "constrained_columns": column_names,
            }
        return self._value_or_raise(data, table_name, schema)

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

    def _index_query(self, owner):
        """
        Override _index_query to optimize performance in OceanBase Oracle mode.

        Key optimization: Add filtering on all_ind_columns.table_name to reduce
        the amount of data scanned early in the query execution.

        Only for sqlalchemy 2.x compatibility.
        """
        if not _dictionary_has_ind_expressions:
            parent_query = super()._index_query
            # The instance cache already owns this result. Avoid retaining
            # this dialect in SQLAlchemy's class-level LRU cache as well.
            uncached_query = getattr(parent_query, "__wrapped__", None)
            if uncached_query is not None:
                return uncached_query(self, owner)
            return parent_query(owner)
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
