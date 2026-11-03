import argparse
import json
from contextlib import closing
from pathlib import Path

from tracepost import query, store


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="tracepost", description="Local creator metrics hub")
    parser.add_argument("--db", type=Path, default=store.default_db(), help="SQLite path (default: %(default)s)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("demo", help="seed synthetic demo data into an empty database")
    sub.add_parser("status", help="sync status as JSON")
    ls = sub.add_parser("list", help="contents with latest metrics as JSON")
    ls.add_argument("--platform", choices=["douyin", "xiaohongshu"])
    serve = sub.add_parser("serve", help="local web dashboard + JSON API")
    serve.add_argument("--port", type=int, default=8765)
    sub.add_parser("mcp", help="MCP server over stdio (read-only tools)")
    args = parser.parse_args(argv)

    if args.cmd == "serve":
        import uvicorn

        from tracepost.web import create_app

        uvicorn.run(create_app(args.db), host="127.0.0.1", port=args.port)
        return
    if args.cmd == "mcp":
        from tracepost.mcp_server import build_server

        build_server(args.db).run("stdio")
        return

    with closing(store.connect(args.db)) as conn:
        if args.cmd == "demo":
            from tracepost import demo

            demo.seed(conn)
            print(f"demo data written to {args.db}")
            return
        result = query.status(conn) if args.cmd == "status" else query.list_contents(conn, args.platform)
    print(json.dumps(result, ensure_ascii=False, indent=2))
