from contextlib import closing
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from tracepost import query, store

STATIC = Path(__file__).parent / "static"


def create_app(db_path: Path) -> FastAPI:
    app = FastAPI(title="tracepost")
    # Host allow-list blocks DNS-rebinding pages from reading the local API.
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])

    @app.get("/api/status")
    def api_status() -> dict:
        with closing(store.connect(db_path)) as conn:
            return query.status(conn)

    @app.get("/api/contents")
    def api_contents(platform: str | None = None) -> dict:
        with closing(store.connect(db_path)) as conn:
            return query.list_contents(conn, platform)

    if (STATIC / "index.html").exists():
        app.frontend("/", directory=STATIC)
    return app
