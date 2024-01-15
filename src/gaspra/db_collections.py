from typing import Callable

from sqlite3 import Connection

from gaspra.db_connections import connection_factory as default_connection_factory

SELECT = """
SELECT data
FROM {table}
WHERE tag = ?
"""

LENGTH = """
SELECT count(*)
FROM {table}
"""

DELETE = """
DELETE
FROM {table}
WHERE tag = ?
"""

INSERT = """
INSERT INTO {table} (tag, data) VALUES(?,?)
ON CONFLICT (tag)
DO
  UPDATE SET data=excluded.data
"""

ITER = """
SELECT tag
FROM {table}
"""


class DBCollection:
    table: str
    connection_factory: Callable[[], Connection]

    def __init__(self, table: str, connection_factory=default_connection_factory):
        self.table = table
        self.connection_factory = connection_factory
        with self.connection_factory() as connection:
            cursor = connection.cursor()
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            cursor.execute(f"CREATE TABLE {table} (tag TEXT PRIMARY KEY, data BLOB)")

    def __getitem__(self, tag: str):
        statement = SELECT.format(table=self.table)
        with self.connection_factory() as connection:
            result = connection.cursor().execute(statement, (tag,)).fetchone()
            if result is not None:
                return result[0]
            else:
                raise KeyError(tag)

    def __setitem__(self, tag: str, contents: bytes):
        statement = INSERT.format(table=self.table)
        with self.connection_factory() as connection:
            connection.cursor().execute(statement, (tag, contents))

    def __delitem__(self, tag: str):
        statement = DELETE.format(table=self.table)
        with self.connection_factory() as connection:
            if connection.cursor().execute(statement, (tag,)).rowcount == 0:
                raise KeyError(tag)

    def __iter__(self):
        statement = ITER.format(table=self.table)
        with self.connection_factory() as connection:
            result = connection.cursor().execute(statement)
            for row in result:
                yield row[0]

    def __len__(self):
        statement = LENGTH.format(table=self.table)
        with self.connection_factory() as connection:
            return connection.cursor().execute(statement).fetchone()[0]

    def __contains__(self, tag):
        statement = SELECT.format(table=self.table)
        with self.connection_factory() as connection:
            return connection.cursor().execute(statement, (tag,)).fetchone() is not None
