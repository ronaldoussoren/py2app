import typing

from modulegraph.modulegraph import ModuleGraph

from .. import build_app
from ._types import RecipeInfo

# __import__ in sqlalchemy.dialects
ENGINE_DEPS = {
    "asyncpg": ("asyncpg",),
    "psycopg2cffi": ("psycopg2cffi",),
    "pg8000": ("pg8000",),
    "firebird": ("sqlalchemy_firebird",),
    "sybase": "sqlalchemy_sybase",
    "aiosqlite": ("aiosqlite", "sqlite3"),
    "oursql": ("oursql",),
    "aiomysql": ("oursql", "pymysql"),
    "mariadb": ("mariadb",),
    "mysqldb": ("MySQLdb",),
    "cymysql": ("cymysql",),
    "pymssql": ("pymssql",),
    "fdb": ("fdb",),
    "kinterbasdb": ("kinterbasdb",),
}

# __import__ in sqlalchemy.connectors
CONNECTOR_DEPS = {
    "pyodbc": ("pyodbc",),
}


def check(cmd: "build_app.py2app", mf: ModuleGraph) -> typing.Optional[RecipeInfo]:
    m = mf.findNode("sqlalchemy")
    if m is None or m.filename is None:
        return None

    for deps in ENGINE_DEPS.values():
        for mod in deps:
            try:
                mf.import_hook(mod, m)
            except ImportError:
                pass

    for deps in CONNECTOR_DEPS.values():
        for mod in deps:
            try:
                mf.import_hook(mod, m)
            except ImportError:
                pass

    return {"packages": ["sqlalchemy"]}
