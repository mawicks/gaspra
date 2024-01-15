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

SELECT_ANYTHING = """
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

CHANGE_PARENT = """
UPDATE graph
SET parent = ?, parent_rid = ?
WHERE rowid = ?
"""

ADD_CHILDx = """
UPDATE graph SET child{x}_rid = ? WHERE rowid = ?
"""

REMOVE_IF_CHILDx = """
UPDATE graph
SET child{x}_rid = NULL
WHERE rowid = ? AND child{x}_rid = ?
"""

GET_START_PATH = """
SELECT height, rowid
FROM graph
WHERE tag = ?
"""

GET_BEST_PATH = """
WITH current AS (
    SELECT *
    FROM graph
    WHERE rowid = ?
),
children AS (
    SELECT child.*,
        child.rowid AS child_rowid
    FROM current
        JOIN graph child ON child.rowid = current.child0_rid
    UNION ALL
    SELECT child.*,
        child.rowid AS child_rowid
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
FROM best_path
WHERE best_path.priority = 1
"""

GET_NODE_METRICS = """
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

UPDATE_METRICS = """
UPDATE graph
SET
    height = ?,
    size = ?
WHERE
    rowid = ?
"""

OLD_START_PATH = """
SELECT height, rowid
FROM graph
WHERE tag = ?
"""

OLD_GET_BEST_PATH = """
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

OLD_UPDATE_METRICS = """
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
