"""DSN parsing: OceanBase two-part / three-part without manual percent-encoding."""

from __future__ import annotations

from oceanbase_cli.dsn import parse_mysql_url


def test_simple_oceanbase() -> None:
    cfg = parse_mysql_url("oceanbase://u:p@10.0.0.1:3881/mydb")
    assert cfg.user == "u"
    assert cfg.password == "p"
    assert cfg.host == "10.0.0.1"
    assert cfg.port == 3881
    assert cfg.database == "mydb"


def test_two_part_unencoded() -> None:
    cfg = parse_mysql_url(
        "oceanbase://mysqluser@mytenant:mypass@192.168.0.5:3881/odb"
    )
    assert cfg.user == "mysqluser@mytenant"
    assert cfg.password == "mypass"
    assert cfg.host == "192.168.0.5"
    assert cfg.database == "odb"


def test_three_part_unencoded_hash() -> None:
    cfg = parse_mysql_url(
        "oceanbase://mysqluser@mytenant#mycluster:Secret@x@192.168.1.10:3881/appdb"
    )
    assert cfg.user == "mysqluser@mytenant#mycluster"
    assert cfg.password == "Secret@x"
    assert cfg.host == "192.168.1.10"
    assert cfg.database == "appdb"


def test_preencoded_no_double_encode() -> None:
    cfg = parse_mysql_url(
        "oceanbase://mysqluser%40tenant%23cluster:pw%40d@10.0.0.2:2881/db"
    )
    assert cfg.user == "mysqluser@tenant#cluster"
    assert cfg.password == "pw@d"


def test_mysql_scheme_unchanged() -> None:
    cfg = parse_mysql_url("mysql://a:b@h:3306/d")
    assert cfg.user == "a"
    assert cfg.host == "h"
