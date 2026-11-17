"""Binding regressions at the SQLAlchemy-to-DBAPI boundary, without a server."""

import importlib
import sys
import types
from unittest import mock

import pytest
import sqlalchemy as sa


@pytest.fixture(params=["cx_oracle", "cx_oceanbase"])
def dbapi_engine(request, monkeypatch):
    # Package initialization eagerly imports the optional native driver. Only
    # stub that import; execution below uses SQLAlchemy's real dialect/context.
    with mock.patch.dict(
        sys.modules, {"cx_Oceanbase": types.ModuleType("cx_Oceanbase")}
    ):
        importlib.import_module("oceanbase_sqlalchemy." + request.param)

    dbapi = mock.Mock(paramstyle="named", version="8.3.0")
    dbapi.__future__ = types.SimpleNamespace(dml_ret_array_val=False)
    dbapi.Error = type("DBAPIError", (Exception,), {})
    dbapi.DatabaseError = type("DatabaseError", (dbapi.Error,), {})
    cursor = dbapi.connect.return_value.cursor.return_value
    cursor.description = None
    cursor.rowcount = 1

    engine = sa.create_engine("oceanbase+" + request.param + "://", module=dbapi)
    # Bypass server discovery, while retaining compilation, parameter mapping,
    # pre_exec, and the actual execute/executemany calls into the mock DBAPI.
    monkeypatch.setattr(engine.dialect, "initialize", lambda connection: None)
    try:
        yield engine, cursor
    finally:
        engine.dispose()


@pytest.mark.parametrize(
    "name, rendered_name",
    [
        ("姓名", '"姓名"'),
        ("p姓名", '"p姓名"'),
        ("姓名_1", '"姓名_1"'),
        ("start", "start"),
        ("START", "START"),
        ("end", "end"),
        ("p_name", "p_name"),
    ],
)
def test_text_bind_names_and_parameter_keys(dbapi_engine, name, rendered_name):
    engine, cursor = dbapi_engine
    with engine.connect() as connection:
        connection.execute(sa.text("UPDATE demo SET name=:" + name), {name: "张三"})

    cursor.execute.assert_called_once_with(
        "UPDATE demo SET name=:" + rendered_name, {rendered_name: "张三"}
    )


def test_mixed_and_repeated_binds_reuse_statement(dbapi_engine):
    engine, cursor = dbapi_engine
    statement = sa.text(
        "UPDATE demo SET name=:姓名, alias=:p姓名 "
        "WHERE id BETWEEN :start AND :end OR name=:姓名"
    )
    expected_sql = (
        'UPDATE demo SET name=:"姓名", alias=:"p姓名" '
        'WHERE id BETWEEN :start AND :end OR name=:"姓名"'
    )
    with engine.connect() as connection:
        for value in ["张三", "李四"]:
            connection.execute(
                statement, {"姓名": value, "p姓名": value, "start": 1, "end": 2}
            )

    assert cursor.execute.call_args_list == [
        mock.call(
            expected_sql, {'"姓名"': value, '"p姓名"': value, "start": 1, "end": 2}
        )
        for value in ["张三", "李四"]
    ]


def test_executemany_maps_every_parameter_set(dbapi_engine):
    engine, cursor = dbapi_engine
    with engine.connect() as connection:
        connection.execute(
            sa.text("UPDATE demo SET name=:姓名 WHERE id=:start"),
            [{"姓名": "张三", "start": 1}, {"姓名": "李四", "start": 2}],
        )

    cursor.executemany.assert_called_once_with(
        'UPDATE demo SET name=:"姓名" WHERE id=:start',
        [{'"姓名"': "张三", "start": 1}, {'"姓名"': "李四", "start": 2}],
    )


@pytest.mark.parametrize("operation", ["insert", "update"])
def test_generated_dml_binds(dbapi_engine, operation):
    engine, cursor = dbapi_engine
    table = sa.Table(
        "demo",
        sa.MetaData(),
        sa.Column("姓名", sa.String(20)),
        sa.Column("start", sa.String(20)),
    )
    statement = getattr(table, operation)()
    with engine.connect() as connection:
        connection.execute(statement, {"姓名": "张三", "start": "before"})

    expected_sql = {
        "insert": 'INSERT INTO demo ("姓名", "start") VALUES (:"姓名", :start)',
        "update": 'UPDATE demo SET "姓名"=:"姓名", "start"=:start',
    }[operation]
    cursor.execute.assert_called_once_with(
        expected_sql, {'"姓名"': "张三", "start": "before"}
    )


@pytest.mark.parametrize("name", ["姓名", "p姓名", "start"])
def test_explicit_quote_preserves_unicode_and_reserved_word_fix(dbapi_engine, name):
    engine, cursor = dbapi_engine
    statement = sa.text("UPDATE demo SET name=:" + name).bindparams(
        sa.bindparam(name, quote=True)
    )
    rendered_name = "start" if name == "start" else '"' + name + '"'
    with engine.connect() as connection:
        connection.execute(statement, {name: "张三"})

    cursor.execute.assert_called_once_with(
        "UPDATE demo SET name=:" + rendered_name, {rendered_name: "张三"}
    )


@pytest.mark.parametrize("name", ["123start", "_name"])
def test_ascii_prefix_normalization(dbapi_engine, name):
    engine, cursor = dbapi_engine
    rendered_name = "D" + name if sa.__version__.startswith("2.") else name
    with engine.connect() as connection:
        connection.execute(sa.text("UPDATE demo SET name=:" + name), {name: "value"})

    cursor.execute.assert_called_once_with(
        "UPDATE demo SET name=:" + rendered_name, {rendered_name: "value"}
    )


def test_expanding_reserved_word_bind(dbapi_engine):
    engine, cursor = dbapi_engine
    statement = sa.text("UPDATE demo SET name=:value WHERE id IN :start").bindparams(
        sa.bindparam("start", expanding=True)
    )
    with engine.connect() as connection:
        connection.execute(statement, {"value": "changed", "start": [1, 2]})

    cursor.execute.assert_called_once_with(
        "UPDATE demo SET name=:value WHERE id IN (:start_1, :start_2)",
        {"value": "changed", "start_1": 1, "start_2": 2},
    )
