"""Exercise single-table reflection against a local dictionary fixture."""

import sys
import types
from unittest import mock

import pytest
import sqlalchemy as sa
from sqlalchemy.sql import quoted_name


@pytest.fixture
def dialect(monkeypatch):
    monkeypatch.setitem(sys.modules, "cx_Oceanbase", types.ModuleType("cx_Oceanbase"))
    from oceanbase_sqlalchemy.cx_oracle import OceanBaseDialect_cx_oracle

    result = OceanBaseDialect_cx_oracle()
    result.default_schema_name = "app"
    result.server_version_info = (11, 2, 0, 0)
    return result


@pytest.fixture
def dictionary_inspector(dialect):
    if not sa.__version__.startswith("2."):
        pytest.skip("Requires SQLAlchemy 2.x dictionary reflection")

    from sqlalchemy.dialects.oracle.dictionary import DB_LINK_PLACEHOLDER

    dictionary_sql = """
    CREATE TABLE "all_objects{suffix}" (
        owner, object_name, object_type
    );
    CREATE TABLE "all_constraints{suffix}" (
        owner, table_name, constraint_name, constraint_type, r_owner,
        r_constraint_name, search_condition, delete_rule
    );
    CREATE TABLE "all_cons_columns{suffix}" (
        owner, table_name, constraint_name, column_name, position
    );
    CREATE TABLE "all_tab_cols{suffix}" (
        owner, table_name, column_name, data_type, char_length, data_length, data_precision,
        data_scale, nullable, data_default, virtual_column, hidden_column, column_id
    );
    CREATE TABLE "all_col_comments{suffix}" (owner, table_name, column_name, comments);

    INSERT INTO "all_objects{suffix}" VALUES
        ('APP', 'MixedCase', 'TABLE'), ('APP', 'NO_KEY', 'VIEW'),
        ('OTHER', 'MixedCase', 'TABLE'), ('APP', 'ONLY_SEQUENCE', 'SEQUENCE');
    INSERT INTO "all_constraints{suffix}" VALUES
        ('APP', 'MixedCase', 'PK_DEMO', 'P', NULL, NULL, NULL, NULL),
        ('APP', 'MixedCase', 'U_DEMO', 'U', NULL, NULL, NULL, NULL),
        ('OTHER', 'MixedCase', 'PK_DEMO', 'P', NULL, NULL, NULL, NULL);
    INSERT INTO "all_cons_columns{suffix}" VALUES
        ('APP', 'MixedCase', 'PK_DEMO', 'FIRST_IN_TABLE', 2),
        ('APP', 'MixedCase', 'PK_DEMO', 'SecondInTable', 1),
        ('APP', 'MixedCase', 'U_DEMO', 'NOT_PK', 1),
        ('OTHER', 'MixedCase', 'PK_DEMO', 'OTHER_ID', 1);
    INSERT INTO "all_tab_cols{suffix}" VALUES
        ('APP', 'MixedCase', 'FIRST_IN_TABLE', 'NUMBER', NULL, 22, 18, 0, 'N', NULL, 'NO', 'NO', 1),
        ('APP', 'MixedCase', 'SecondInTable', 'DATE', NULL, 7, NULL, NULL, 'N', 'SYSDATE', 'NO', 'NO', 2),
        ('APP', 'MixedCase', 'HIDDEN_COL', 'NUMBER', NULL, 22, NULL, NULL, 'Y', NULL, 'NO', 'YES', 3);
    INSERT INTO "all_col_comments{suffix}" VALUES
        ('APP', 'MixedCase', 'SecondInTable', 'Creation time');
    """
    engine = sa.create_engine("sqlite://")
    with engine.connect() as connection:
        connection.connection.driver_connection.executescript(
            dictionary_sql.format(suffix=DB_LINK_PLACEHOLDER)
        )
        inspector = sa.inspect(connection)
        inspector.dialect = dialect
        statements = []

        def count_statement(conn, cursor, statement, parameters, context, executemany):
            statements.append(statement)

        sa.event.listen(connection, "before_cursor_execute", count_statement)
        yield inspector, statements
    engine.dispose()


def test_inspect_columns_and_primary_key_in_two_queries(dictionary_inspector):
    from sqlalchemy.dialects.oracle import DATE

    inspector, statements = dictionary_inspector
    table_name = quoted_name("MixedCase", True)
    columns = inspector.get_columns(table_name)
    assert [column["name"] for column in columns] == [
        "first_in_table",
        "SecondInTable",
    ]
    assert isinstance(columns[1]["type"], DATE)
    assert columns[1]["nullable"] is False
    assert columns[1]["default"] == "SYSDATE"
    assert columns[1]["comment"] == "Creation time"

    expected_pk = {
        "name": "pk_demo",
        "constrained_columns": ["SecondInTable", "first_in_table"],
    }
    assert inspector.get_pk_constraint(table_name) == expected_pk
    assert inspector.get_pk_constraint(table_name) == expected_pk
    assert len(statements) == 2
    assert "search_condition" not in statements[-1]


def test_primary_key_distinguishes_empty_and_missing(dictionary_inspector):
    inspector, statements = dictionary_inspector
    assert inspector.get_pk_constraint("no_key") == {
        "name": None,
        "constrained_columns": [],
    }
    with pytest.raises(sa.exc.NoSuchTableError, match="only_sequence"):
        inspector.get_pk_constraint("only_sequence")
    assert inspector.get_pk_constraint(
        quoted_name("MixedCase", True), schema="other"
    ) == {
        "name": "pk_demo",
        "constrained_columns": ["other_id"],
    }
    assert len(statements) == 3


@pytest.mark.parametrize(
    "options",
    [
        {"oracle_resolve_synonyms": True},
        {"dblink": "remote"},
        pytest.param(
            {},
            marks=pytest.mark.skipif(
                sa.__version__.startswith("2."),
                reason="Legacy reflection is used on SQLAlchemy 1.x",
            ),
        ),
    ],
)
def test_primary_key_delegates_extended_reflection_options(dialect, options):
    parent = type(dialect).__bases__[0]
    with mock.patch.object(
        parent, "get_pk_constraint", return_value=mock.sentinel.pk
    ) as reflect:
        result = dialect.get_pk_constraint(None, "demo", schema="app", **options)
        assert result is mock.sentinel.pk
        reflect.assert_called_once_with(None, "demo", schema="app", **options)
