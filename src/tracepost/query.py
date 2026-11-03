"""Read-only queries shared by Web, CLI and MCP so every surface returns the same numbers."""

import json
import sqlite3

SCHEMA_VERSION = 1


def _metrics(conn: sqlite3.Connection, snapshot_id: int) -> dict:
    rows = conn.execute(
        "SELECT name, raw_name, value, unit, definition, missing_reason FROM metric WHERE snapshot_id = ?",
        (snapshot_id,),
    )
    return {r["name"]: {k: r[k] for k in r.keys() if k != "name"} for r in rows}


def status(conn: sqlite3.Connection) -> dict:
    platforms = []
    for (platform,) in conn.execute("SELECT DISTINCT platform FROM account ORDER BY platform"):
        last = conn.execute(
            "SELECT * FROM sync_run WHERE platform = ? ORDER BY started_at DESC LIMIT 1", (platform,)
        ).fetchone()
        last_ok = conn.execute(
            "SELECT finished_at FROM sync_run WHERE platform = ? AND status = 'success' "
            "ORDER BY finished_at DESC LIMIT 1",
            (platform,),
        ).fetchone()
        count = conn.execute("SELECT count(*) FROM content WHERE platform = ?", (platform,)).fetchone()[0]
        platforms.append(
            {
                "platform": platform,
                "content_count": count,
                "last_run": dict(last) | {"warnings": json.loads(last["warnings"])} if last else None,
                "last_success_at": last_ok["finished_at"] if last_ok else None,
            }
        )
    return {"schema_version": SCHEMA_VERSION, "platforms": platforms}


def list_contents(conn: sqlite3.Connection, platform: str | None = None) -> dict:
    """Each content with its latest observation. Missing metrics keep value=null and a reason."""
    rows = conn.execute(
        """
        SELECT c.*, g.label AS group_label, m.group_id,
               s.snapshot_id, s.collected_at, s.source, s.sync_run_id, s.period_start, s.period_end
        FROM content c
        LEFT JOIN content_group_member m USING (platform, id_namespace, content_id)
        LEFT JOIN content_group g ON g.group_id = m.group_id
        LEFT JOIN snapshot s ON s.snapshot_id = (
            SELECT snapshot_id FROM snapshot x
            WHERE x.platform = c.platform AND x.id_namespace = c.id_namespace AND x.content_id = c.content_id
            ORDER BY x.collected_at DESC LIMIT 1)
        WHERE ?1 IS NULL OR c.platform = ?1
        ORDER BY c.published_at DESC
        """,
        (platform,),
    ).fetchall()
    items = []
    for r in rows:
        item = {k: r[k] for k in r.keys() if k != "snapshot_id"}
        item["metrics"] = _metrics(conn, r["snapshot_id"]) if r["snapshot_id"] else {}
        items.append(item)
    return {"schema_version": SCHEMA_VERSION, "items": items}
