# AGENTS.md

Guidance for AI coding agents and contributors working in this repository.

## Layout

- `src/tracepost/store.py`: SQLite schema. The `CHECK` and `UNIQUE` constraints encode the data invariants; do not weaken them to make an adapter pass.
- `src/tracepost/query.py`: the only read path. Web (`web.py`), CLI (`cli.py`) and MCP (`mcp_server.py`) must call it rather than run their own SQL.
- `src/tracepost/demo.py`: synthetic data. Titles start with `[DEMO]`; it is never evidence that real collection works.
- `frontend/`: Vite + React + TypeScript. `npm run build` writes to `src/tracepost/static/` (git-ignored).
- `docs/specs/` is the product spec, `docs/plans/` the living plan (update progress, decisions and evidence there), and `docs/research/` holds evidence.

## Commands

```bash
uv run pytest -q
npm --prefix frontend run lint
npm --prefix frontend run build
```

## Rules

- Missing value: `null` plus `missing_reason`. Never coerce to `0`. A real `0` stays `0`.
- Keep `collected_at` (our observation time) separate from the platform's statistic period.
- Read-only tools must stay read-only. Anything that logs in, syncs or writes gets its own tool, explicit opt-in, and a profile lock.
- Never commit or log cookies, auth headers, browser profiles, real account data or `.sqlite` files. Test fixtures must be synthetic or redacted.
- Collect only through the official API, the platform's own export, or responses the page loads during normal browsing. No captcha bypass, signature reverse engineering, stealth plugins or cookie replay. Stop and return `user_action_required` instead.
- License hygiene: copy code only from MIT/BSD/Apache-compatible sources, and record each source in `THIRD_PARTY_NOTICES.md` (repo, commit, license, files). Never copy from AGPL, non-commercial or unlicensed projects. See the reuse table in the v0.1 plan.
- Dependencies: `pyproject.toml` and `uv.lock` must resolve against public PyPI. Do not commit local mirror indexes. Use `uv lock --default-index https://pypi.org/simple` if your machine is configured with a mirror.
- MCP SDK is 2.x (`mcp.server.mcpserver.MCPServer`); type tool returns (e.g. `dict[str, Any]`) so results include `structuredContent`.
