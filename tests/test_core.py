import asyncio
import sqlite3

import pytest
from fastapi.testclient import TestClient

from tracepost import demo, query, store
from tracepost.mcp_server import build_server
from tracepost.web import create_app


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "t.sqlite"
    conn = store.connect(path)
    demo.seed(conn)
    yield path, conn
    conn.close()


def test_latest_snapshot_keeps_null_reason_and_real_zero(db):
    _, conn = db
    items = {i["content_id"]: i for i in query.list_contents(conn)["items"]}
    note = items["demo-note-001"]
    assert note["collected_at"].startswith("2026-11-02")  # latest of two observations
    assert note["metrics"]["shares"]["value"] == 0
    missing = items["demo-note-002"]["metrics"]["impressions"]
    assert missing["value"] is None and missing["missing_reason"] == "not_exposed"
    assert note["group_label"] == items["demo-video-001"]["group_label"]


def test_null_without_reason_is_rejected(db):
    _, conn = db
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO metric (snapshot_id, name, value) VALUES (1, 'saves', NULL)")


def test_same_run_retry_does_not_duplicate_snapshot(db):
    _, conn = db
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO snapshot (sync_run_id, platform, account_id, id_namespace, content_id, collected_at, source) "
            "VALUES ('demo-xhs-1', 'xiaohongshu', 'demo-account', 'web', 'demo-note-001', 'x', 'demo')"
        )


def test_demo_refuses_non_empty_db(db):
    _, conn = db
    with pytest.raises(SystemExit):
        demo.seed(conn)


def test_web_matches_shared_query_and_rejects_foreign_host(db):
    path, conn = db
    client = TestClient(create_app(path), base_url="http://127.0.0.1")
    assert client.get("/api/contents").json() == query.list_contents(conn)
    assert client.get("/api/status").json()["schema_version"] == query.SCHEMA_VERSION
    assert client.get("/api/status", headers={"host": "evil.example"}).status_code == 400


def test_mcp_tools_are_read_only_and_structured(db):
    path, conn = db
    server = build_server(path)
    tools = asyncio.run(server.list_tools())
    assert {t.name for t in tools} == {"status", "list_contents"}
    assert all(t.annotations.read_only_hint for t in tools)
    result = asyncio.run(server.call_tool("list_contents", {"platform": "douyin"}))
    assert result.structured_content == query.list_contents(conn, "douyin")
