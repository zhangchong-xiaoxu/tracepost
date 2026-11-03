from contextlib import closing
from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from tracepost import query, store

# Hint only; the real guarantee is that no tool here writes or touches a platform.
READ_ONLY = ToolAnnotations(read_only_hint=True, open_world_hint=False)


def build_server(db_path: Path) -> MCPServer:
    server = MCPServer(
        "tracepost",
        instructions="Query locally stored creator metrics (Douyin, Xiaohongshu). "
        "Tools only read local snapshots; they never log in or fetch from platforms. "
        "A null metric value always comes with missing_reason; check collected_at for freshness.",
    )

    @server.tool(annotations=READ_ONLY)
    def status() -> dict[str, Any]:
        """Per-platform sync status, last successful sync and content counts."""
        with closing(store.connect(db_path)) as conn:
            return query.status(conn)

    @server.tool(annotations=READ_ONLY)
    def list_contents(platform: str | None = None) -> dict[str, Any]:
        """Contents with their latest metrics. platform: 'douyin' or 'xiaohongshu'; omit for all."""
        with closing(store.connect(db_path)) as conn:
            return query.list_contents(conn, platform)

    return server
