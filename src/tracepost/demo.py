"""Synthetic demo data. Clearly fake; never evidence that real collection works."""

import sqlite3

RUNS = [
    ("demo-xhs-1", "xiaohongshu", "2026-11-01T09:00:00+08:00"),
    ("demo-xhs-2", "xiaohongshu", "2026-11-02T09:00:00+08:00"),
    ("demo-dy-1", "douyin", "2026-11-02T09:05:00+08:00"),
]

CONTENTS = [
    ("xiaohongshu", "web", "demo-note-001", "note", "[DEMO] 家用 NAS 入门清单", "2026-10-31T20:00:00+08:00"),
    ("xiaohongshu", "web", "demo-note-002", "note", "[DEMO] 一人公司周复盘", "2026-10-25T20:00:00+08:00"),
    ("douyin", "web", "demo-video-001", "video", "[DEMO] 家用 NAS 入门清单", "2026-10-31T21:00:00+08:00"),
]

# (run_id, platform, content_id or '' for account, {name: (value, unit, missing_reason)})
SNAPSHOTS = [
    ("demo-xhs-1", "xiaohongshu", "demo-note-001", {"views": (820, "count", None), "likes": (41, "count", None)}),
    ("demo-xhs-2", "xiaohongshu", "demo-note-001", {"views": (1530, "count", None), "likes": (88, "count", None),
                                                   "shares": (0, "count", None)}),
    ("demo-xhs-2", "xiaohongshu", "demo-note-002", {"views": (310, "count", None),
                                                   "impressions": (None, "count", "not_exposed")}),
    ("demo-dy-1", "douyin", "demo-video-001", {"views": (2400, "count", None), "likes": (96, "count", None),
                                              "completion_rate": (0.31, "ratio", None)}),
    ("demo-xhs-1", "xiaohongshu", "", {"followers_total": (1200, "count", None)}),
    ("demo-xhs-2", "xiaohongshu", "", {"followers_total": (1236, "count", None)}),
    ("demo-dy-1", "douyin", "", {"followers_total": (530, "count", None)}),
]


def seed(conn: sqlite3.Connection) -> None:
    if conn.execute("SELECT count(*) FROM content").fetchone()[0]:
        raise SystemExit("refusing to seed demo data into a non-empty database; use a separate --db")
    with conn:
        for platform in ("xiaohongshu", "douyin"):
            conn.execute("INSERT INTO account VALUES (?, 'demo-account', '[DEMO] account')", (platform,))
        for run_id, platform, at in RUNS:
            conn.execute(
                "INSERT INTO sync_run (run_id, platform, account_id, started_at, finished_at, status, scope) "
                "VALUES (?, ?, 'demo-account', ?, ?, 'success', 'demo')",
                (run_id, platform, at, at),
            )
        for platform, ns, cid, kind, title, published in CONTENTS:
            conn.execute(
                "INSERT INTO content VALUES (?, ?, ?, 'demo-account', ?, ?, NULL, ?)",
                (platform, ns, cid, kind, title, published),
            )
        gid = conn.execute("INSERT INTO content_group (label) VALUES ('[DEMO] 家用 NAS 入门清单')").lastrowid
        conn.executemany(
            "INSERT INTO content_group_member VALUES (?, ?, 'web', ?)",
            [(gid, "xiaohongshu", "demo-note-001"), (gid, "douyin", "demo-video-001")],
        )
        collected = {run_id: at for run_id, _, at in RUNS}
        for run_id, platform, cid, metrics in SNAPSHOTS:
            sid = conn.execute(
                "INSERT INTO snapshot (sync_run_id, platform, account_id, id_namespace, content_id, collected_at, source) "
                "VALUES (?, ?, 'demo-account', ?, ?, ?, 'demo')",
                (run_id, platform, "web" if cid else "", cid, collected[run_id]),
            ).lastrowid
            conn.executemany(
                "INSERT INTO metric (snapshot_id, name, value, unit, missing_reason) VALUES (?, ?, ?, ?, ?)",
                [(sid, name, *v) for name, v in metrics.items()],
            )
