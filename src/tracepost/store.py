"""Local SQLite store. Schema encodes the data invariants from docs/specs."""

import os
import sqlite3
import sys
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS account (
    platform     TEXT NOT NULL,
    account_id   TEXT NOT NULL,
    display_name TEXT,
    PRIMARY KEY (platform, account_id)
);

CREATE TABLE IF NOT EXISTS content (
    platform     TEXT NOT NULL,
    id_namespace TEXT NOT NULL,  -- web id and open-API id are not assumed equal
    content_id   TEXT NOT NULL,
    account_id   TEXT NOT NULL,
    kind         TEXT,
    title        TEXT,
    url          TEXT,
    published_at TEXT,
    PRIMARY KEY (platform, id_namespace, content_id)
);

-- Cross-platform links are explicit user decisions, never title matching.
CREATE TABLE IF NOT EXISTS content_group (
    group_id INTEGER PRIMARY KEY,
    label    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS content_group_member (
    group_id     INTEGER NOT NULL REFERENCES content_group (group_id) ON DELETE CASCADE,
    platform     TEXT NOT NULL,
    id_namespace TEXT NOT NULL,
    content_id   TEXT NOT NULL,
    PRIMARY KEY (platform, id_namespace, content_id)
);

CREATE TABLE IF NOT EXISTS sync_run (
    run_id      TEXT PRIMARY KEY,
    platform    TEXT NOT NULL,
    account_id  TEXT NOT NULL,
    started_at  TEXT NOT NULL,
    finished_at TEXT,
    status      TEXT NOT NULL CHECK (status IN
        ('running', 'success', 'partial', 'failed', 'user_action_required')),
    scope       TEXT,
    warnings    TEXT NOT NULL DEFAULT '[]'  -- JSON array
);

CREATE TABLE IF NOT EXISTS snapshot (
    snapshot_id  INTEGER PRIMARY KEY,
    sync_run_id  TEXT NOT NULL REFERENCES sync_run (run_id),
    platform     TEXT NOT NULL,
    account_id   TEXT NOT NULL,
    id_namespace TEXT NOT NULL DEFAULT '',
    content_id   TEXT NOT NULL DEFAULT '',  -- '' = account-level snapshot (followers etc.)
    collected_at TEXT NOT NULL,             -- when we observed it
    period_start TEXT,                      -- platform statistic window, if any
    period_end   TEXT,
    timezone     TEXT,
    source       TEXT NOT NULL,             -- e.g. official_api, export_file, page_response, dom, demo
    UNIQUE (sync_run_id, platform, account_id, id_namespace, content_id)
);

CREATE TABLE IF NOT EXISTS metric (
    snapshot_id    INTEGER NOT NULL REFERENCES snapshot (snapshot_id) ON DELETE CASCADE,
    name           TEXT NOT NULL,
    raw_name       TEXT,
    value          REAL,
    unit           TEXT,
    definition     TEXT,
    missing_reason TEXT,
    PRIMARY KEY (snapshot_id, name),
    -- missing is NULL plus a reason; a real 0 stays 0
    CHECK ((value IS NULL) = (missing_reason IS NOT NULL))
);
"""


def default_home() -> Path:
    if env := os.environ.get("TRACEPOST_HOME"):
        return Path(env)
    if sys.platform == "win32":
        return Path(os.environ.get("LOCALAPPDATA", Path.home())) / "tracepost"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "tracepost"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "tracepost"


def default_db() -> Path:
    return default_home() / "tracepost.sqlite"


def connect(path: str | os.PathLike[str]) -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn
