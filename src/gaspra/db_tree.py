from typing import Callable
from collections.abc import Hashable, Sequence

from sqlite3 import Connection
from gaspra.db_tree_sql import (
    CHANGE_PARENT,
    CREATE_GRAPH,
    GET_BEST_PATH,
    GET_NODE_METRICS,
    GET_START_PATH,
    GRAPH_INDEX1,
    GRAPH_INDEX2,
    INSERT,
    OLD_GET_BEST_PATH,
    OLD_START_PATH,
    OLD_UPDATE_METRICS,
    PATH_TO,
    SELECT_ANYTHING,
    UPDATE_METRICS,
    ADD_CHILDx,
    REMOVE_IF_CHILDx,
)

from gaspra.db_connections import connection_factory as default_connection_factory


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
        statement = SELECT_ANYTHING.format(selection="tag")
        with self.connection_factory() as connection:
            return connection.cursor().execute(statement, (tag,)).fetchone() is not None

    def base_version(self, tag) -> Hashable:
        statement = SELECT_ANYTHING.format(selection="base_version")
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
        with self.connection_factory() as connection:
            # Get tag's rowid for use as key in child relationships.
            tag_rid = (
                connection.cursor()
                .execute(SELECT_ANYTHING.format(selection="rowid"), (tag,))
                .fetchone()[0]
            )

            original_parent, original_parent_rid = (
                connection.cursor()
                .execute(SELECT_ANYTHING.format(selection="parent, parent_rid"), (tag,))
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
                .execute(SELECT_ANYTHING.format(selection="rowid"), (new_parent,))
                .fetchone()[0]
            )

            # Point tag to new parent
            connection.cursor().execute(
                CHANGE_PARENT, (new_parent, new_parent_rid, tag_rid)
            )
            # Add tag as child of new parent on childx
            # Heads get added on child0, splits get added on
            child = 0 if original_parent is None else 1
            connection.cursor().execute(
                ADD_CHILDx.format(x=child), (tag_rid, new_parent_rid)
            )

        self._update_metrics(original_parent, original_parent_rid)
        self._update_metrics(new_parent, new_parent_rid)

    def get_split(self, tag: Hashable):
        return self.new_get_split(tag)

    def new_get_split(self, tag: Hashable):
        with self.connection_factory() as connection:
            cursor = connection.cursor()
            depth = 1
            path = [tag]
            height, rowid = cursor.execute(GET_START_PATH, (tag,)).fetchone()
            while depth < height:
                tag, rowid, height = cursor.execute(GET_BEST_PATH, (rowid,)).fetchone()
                path.append(tag)
                depth += 1
        return tag, path

    def _update_metrics(self, tag: str, tag_rid: int):
        self._new_update_metrics(tag, tag_rid)

    def _new_update_metrics(self, tag: str, tag_rid: int):
        with self.connection_factory() as connection:
            while tag_rid is not None:
                _, parent_rid, height, size = connection.execute(
                    GET_NODE_METRICS, (tag_rid,)
                ).fetchone()
                connection.execute(UPDATE_METRICS, (height, size, tag_rid))
                tag_rid = parent_rid

    def old_get_split(self, tag: Hashable):
        with self.connection_factory() as connection:
            cursor = connection.cursor()
            depth = 1
            path = [tag]
            height, rowid = cursor.execute(OLD_START_PATH, (tag,)).fetchone()
            while depth < height:
                tag, rowid, height = cursor.execute(
                    OLD_GET_BEST_PATH, (rowid,)
                ).fetchone()
                path.append(tag)
                depth += 1
        return tag, path

    def _old_update_metrics(self, tag: str, tag_rid: int):
        with self.connection_factory() as connection:
            connection.execute(OLD_UPDATE_METRICS, (tag,))
