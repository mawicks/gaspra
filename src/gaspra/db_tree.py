from typing import Callable
from collections.abc import Hashable, Sequence

from sqlite3 import Connection

from gaspra.db_connections import connection_factory as default_connection_factory

CREATE_GRAPH = """
CREATE TABLE graph (
   tag TEXT,
   parent TEXT,
   height INTEGER,
   size INTEGER,
   base_version TEXT
)
"""
INDEX_GRAPH = """
CREATE INDEX graph_parent ON graph(parent)
"""

INSERT = """
INSERT INTO graph (tag, base_version, height, size)
  VALUES (?, ?, 1, 1)
"""

SELECT = """
SELECT {selection} FROM graph
WHERE tag = ?
"""

PATH_TO = """
WITH RECURSIVE path AS (
   SELECT g.tag, g.parent
   FROM graph g
   WHERE g.tag = ?

   UNION ALL

   SELECT h.tag, h.parent
   FROM graph h
   JOIN path
     ON path.parent = h.tag
)
SELECT tag FROM path
"""


class DBTree:
    connection_factory: Callable[[], Connection]

    def __init__(self, connection_factory=default_connection_factory):
        self.connection_factory = connection_factory
        with self.connection_factory() as connection:
            cursor = connection.cursor()
            for statement in [
                "DROP TABLE IF EXISTS graph",
                CREATE_GRAPH,
                INDEX_GRAPH,
            ]:
                cursor.execute(statement)

    def __contains__(self, tag: Hashable):
        statement = SELECT.format(selection="tag")
        with self.connection_factory() as connection:
            return connection.cursor().execute(statement, (tag,)).fetchone() is not None

    def base_version(self, tag) -> Hashable:
        statement = SELECT.format(selection="base_version")
        with self.connection_factory() as connection:
            return connection.cursor().execute(statement, (tag,)).fetchone()[0]

    def add(self, tag: Hashable, existing_head: Hashable | None = None):
        with self.connection_factory() as connection:
            connection.cursor().execute(INSERT, (tag, existing_head))

    def reverse_path_to(self, tag: Hashable) -> Sequence[Hashable] | None:
        with self.connection_factory() as connection:
            rows = connection.cursor().execute(PATH_TO, (tag,)).fetchall()
            if rows is not None:
                return tuple(row[0] for row in rows)
            else:
                return None

    def path_to(self, tag: Hashable) -> Sequence[Hashable] | None:
        reverse_path = self.reverse_path_to(tag)
        if reverse_path is not None:
            return tuple(tag for tag in reversed(reverse_path))
        else:
            return None

    def change_parent(self, tag, new_parent):
        CHANGE = """
        UPDATE graph SET parent = ?
        WHERE tag = ?
        """
        with self.connection_factory() as connection:
            original_parent = (
                connection.cursor()
                .execute(SELECT.format(selection="parent"), (tag,))
                .fetchone()
            )
            if original_parent is not None:
                original_parent = original_parent[0]
            connection.cursor().execute(CHANGE, (new_parent, tag))
            self._update_metrics(original_parent)
            self._update_metrics(new_parent)

    def get_split(self, tag: Hashable):
        SELECT = """
        SELECT height 
        FROM graph
        WHERE tag = ?
        """

        QUERY = """
        WITH best_path AS (
          SELECT
            g.tag,
            g.height,
            row_number() over 
              (partition by g.parent
               order by height desc, g.rowid desc)   AS priority
          FROM graph g
          WHERE g.parent = ?
        )
        SELECT tag, height from best_path
        WHERE best_path.priority = 1
        """
        with self.connection_factory() as connection:
            cursor = connection.cursor()
            depth = 1
            path = [tag]
            height = cursor.execute(SELECT, (tag,)).fetchone()[0]
            while depth < height:
                x = cursor.execute(QUERY, (tag,)).fetchone()
                if len(x) > 0:
                    tag = x[0]
                    path.append(tag)
                    height = x[1]
                depth += 1
        return tag, path

    def _update_metrics(self, tag):
        UPDATE = """
        WITH subtree AS (
          SELECT
            g.tag,
            coalesce(metrics.size,0) as size,
            coalesce(metrics.height,0) as height
          FROM graph g
          LEFT JOIN (
            SELECT
              sum(size) as size, 
              max(height) as height,
              parent
            FROM graph
            GROUP BY parent
          ) metrics
          ON metrics.parent = g.tag
        )
        UPDATE graph
        SET 
          size = 1 + s.size, 
          height = 1 + s.height
        FROM subtree s
        WHERE graph.tag = s.tag
        AND graph.tag = ?;
        """
        if (reverse_path := self.reverse_path_to(tag)) is None:
            return
        with self.connection_factory() as connection:
            for tag in reverse_path:
                connection.execute(UPDATE, (tag,))
                continue
