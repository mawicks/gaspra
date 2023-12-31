from typing import Callable
from collections.abc import Hashable, Sequence

from sqlite3 import Connection

from gaspra.db_connections import connection_factory as default_connection_factory

CREATE_GRAPH = """
CREATE TABLE graph (
   tag TEXT PRIMARY KEY,
   parent TEXT,
   parent_rid INTEGER,
   child0_rid INTEGER,
   child1_rid INTEGER,
   height INTEGER,
   size INTEGER,
   base_version TEXT
)
"""
GRAPH_INDEX1 = """
CREATE INDEX graph_parent ON graph(parent)
"""
GRAPH_INDEX2 = """
CREATE INDEX graph_parent_rid ON graph(parent_rid)
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
   SELECT g.tag, g.parent_rid
   FROM graph g
   WHERE g.tag = ?

   UNION ALL

   SELECT h.tag, h.parent_rid
   FROM graph h
   JOIN path
     ON path.parent_rid = h.rowid
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
                GRAPH_INDEX1,
                GRAPH_INDEX2,
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
        UPDATE graph SET parent = ?, parent_rid = ?
        WHERE rowid = ?
        """
        ADD_CHILDx = """
        UPDATE graph SET child{x}_rid = ? WHERE rowid = ?
        """
        REMOVE_IF_CHILDx = """
        UPDATE graph SET child{x}_rid = NULL WHERE rowid = ? AND
        child{x}_rid = ?
        """

        with self.connection_factory() as connection:
            # Get tag's rowid for use as key in child relationships.
            tag_rid = (
                connection.cursor()
                .execute(SELECT.format(selection="rowid"), (tag,))
                .fetchone()[0]
            )

            original_parent, original_parent_rid = (
                connection.cursor()
                .execute(SELECT.format(selection="parent, parent_rid"), (tag,))
                .fetchone()
            )

            connection.cursor().execute(
                REMOVE_IF_CHILDx.format(x=0), (original_parent_rid, tag_rid)
            )
            connection.cursor().execute(
                REMOVE_IF_CHILDx.format(x=1), (original_parent_rid, tag_rid)
            )

            # The "new" parent *must* exist.
            new_parent_rid = (
                connection.cursor()
                .execute(SELECT.format(selection="rowid"), (new_parent,))
                .fetchone()[0]
            )

            # Point tag to new parent
            connection.cursor().execute(CHANGE, (new_parent, new_parent_rid, tag_rid))
            # Add tag as child of new parent on childx
            # Heads get added on child0, splits get added on
            child = 0 if original_parent is None else 1
            connection.cursor().execute(
                ADD_CHILDx.format(x=child), (tag_rid, new_parent_rid)
            )

        self._update_metrics(original_parent, original_parent_rid)
        self._update_metrics(new_parent, new_parent_rid)

    def old_get_split(self, tag: Hashable):
        SELECT = """
        SELECT height, rowid 
        FROM graph
        WHERE tag = ?
        """

        QUERY = """
        WITH best_path AS (
        SELECT
            g.tag,
            g.rowid as graph_rowid,
            g.height,
            row_number() over 
            (partition by g.parent_rid
            order by height desc, g.rowid desc)   AS priority
        FROM graph g
        WHERE g.parent_rid = ?
        )
        SELECT tag, graph_rowid, height from best_path
        WHERE best_path.priority = 1
        """
        with self.connection_factory() as connection:
            cursor = connection.cursor()
            depth = 1
            path = [tag]
            height, rowid = cursor.execute(SELECT, (tag,)).fetchone()
            while depth < height:
                tag, rowid, height = cursor.execute(QUERY, (rowid,)).fetchone()
                path.append(tag)
                depth += 1
        return tag, path

    def new_get_split(self, tag: Hashable):
        SELECT = """
        SELECT height, rowid 
        FROM graph
        WHERE tag = ?
        """

        QUERY = """
        WITH current AS (
            SELECT *
            FROM graph
            WHERE rowid = ?
        ),
        children AS (
            SELECT child.*,
                child.rowid as child_rowid
            FROM current
                JOIN graph child ON child.rowid = current.child0_rid
            UNION ALL
            SELECT child.*,
                child.rowid as child_rowid
            FROM current
                JOIN graph child ON child.rowid = current.child1_rid
        ),
        best_path AS (
            SELECT c.tag,
                c.child_rowid,
                c.height,
                row_number() over (
                    order by height desc,
                        child_rowid desc
                ) AS priority
            FROM children c
        )
        SELECT tag,
            child_rowid,
            height
        from best_path
        WHERE best_path.priority = 1
        """
        with self.connection_factory() as connection:
            cursor = connection.cursor()
            depth = 1
            path = [tag]
            height, rowid = cursor.execute(SELECT, (tag,)).fetchone()
            while depth < height:
                tag, rowid, height = cursor.execute(QUERY, (rowid,)).fetchone()
                path.append(tag)
                depth += 1
        return tag, path

    def get_split(self, tag: Hashable):
        return self.new_get_split(tag)

    def _old_update_metrics(self, tag: str, tag_rid: int):
        UPDATE = """
        WITH subtree AS (
          SELECT
            g.tag,
            g.rowid as rid,
            g.parent_rid,
            1 + coalesce(metrics.size,0) as size,
            1 + coalesce(metrics.height,0) as height
          FROM graph g
          LEFT JOIN (
            SELECT
              sum(size) as size, 
              max(height) as height,
              parent_rid
            FROM graph
            GROUP BY parent_rid
          ) metrics
          ON metrics.parent_rid = g.rowid
        ),
        recursive_subtree AS (
            SELECT 
                tag,
                rid,
                parent_rid,
                size,
                height
            FROM subtree
            WHERE tag = ?

            UNION ALL

            SELECT 
                subtree.tag,
                subtree.rid,
                subtree.parent_rid,
                subtree.size,
                subtree.height
            FROM subtree
            JOIN recursive_subtree rst ON subtree.rid = rst.parent_rid
        )
        UPDATE graph
        SET 
            size = (
                SELECT size 
                FROM recursive_subtree 
                WHERE recursive_subtree.tag = graph.tag
            ),
            height = (
                SELECT height 
                FROM recursive_subtree 
                WHERE recursive_subtree.tag = graph.tag
            )
        WHERE 
            tag IN (SELECT tag FROM recursive_subtree);

"""
        with self.connection_factory() as connection:
            connection.execute(UPDATE, (tag,))

    def _new_update_metrics(self, tag: str, tag_rid: int):
        QUERY = """
        WITH current AS (
            SELECT rowid as current_rid,
                *
            FROM graph
            WHERE rowid = ?
        ),
        children AS (
            SELECT current.current_rid,
                current.parent_rid,
                child.height,
                child.size
            FROM current
                LEFT JOIN graph child ON child.rowid = current.child0_rid
            UNION ALL
            SELECT current.current_rid,
                current.parent_rid,
                child.height,
                child.size
            FROM current
                LEFT JOIN graph child ON child.rowid = current.child1_rid
        ),
        metrics AS (
            SELECT current_rid,
                parent_rid,
                1 + coalesce(max(height), 0) as height,
                1 + coalesce(sum(size), 0) as size
            from children
            group by current_rid,
                parent_rid
        )
        SELECT current_rid, parent_rid, height,size
        FROM metrics
        """

        UPDATE = """
        UPDATE graph
        SET
           height = ?,
           size = ?
        WHERE
           rowid = ?
        """

        with self.connection_factory() as connection:
            while tag_rid is not None:
                _, parent_rid, height, size = connection.execute(
                    QUERY, (tag_rid,)
                ).fetchone()
                connection.execute(UPDATE, (height, size, tag_rid))
                tag_rid = parent_rid

    def _update_metrics(self, tag: str, tag_rid: int):
        self._new_update_metrics(tag, tag_rid)
