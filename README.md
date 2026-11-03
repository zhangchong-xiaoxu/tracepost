# tracepost

**Local-first creator analytics for Douyin (抖音) and Xiaohongshu (小红书) — with a dashboard for you and an MCP server for your AI agent.**

[中文说明](#中文说明)

> **Status: early skeleton.** The data model, shared query layer, web dashboard, CLI and read-only MCP server work against a synthetic demo database. **No platform collector is implemented yet**. See the [v0.1 plan](docs/plans/2026-11-03-v0.1.md).

## Why

Creators post the same idea on several platforms, then copy numbers from each creator console by hand. tracepost keeps **your own** post metrics in a local SQLite file, with snapshots over time, and makes them available to:

- **you**, through a local web dashboard;
- **scripts**, through a JSON CLI;
- **AI agents** (Claude Code, Copilot, Cursor, …), through MCP. They can answer questions like "how did last week's note do on both platforms?" without opening a browser.

Design rules the code enforces:

- A missing metric is `null` **with a reason** (`not_exposed`, `login_required`, …); a real `0` stays `0`.
- Every number carries when it was observed and where it came from.
- Cross-platform links are explicit user choices, never title matching.
- Query tools are read-only; nothing logs in or scrapes behind your back.

## Capability matrix

| Capability | Douyin | Xiaohongshu |
| --- | --- | --- |
| Local snapshot store, dashboard, CLI, MCP query | ✅ (demo data) | ✅ (demo data) |
| Collect your own post list and metrics | ⏳ planned | ⏳ planned |
| Follower trend | ⏳ planned | ⏳ planned |
| Comments (read-only) | 💭 later | 💭 later |
| Posting, replying, any platform write | ❌ out of scope | ❌ out of scope |

## Quick start (demo, no account needed)

Requires [uv](https://docs.astral.sh/uv/) and Node.js 20+ (Node is only used to build the dashboard).

```bash
git clone https://github.com/zhangchong-xiaoxu/tracepost && cd tracepost
uv sync
npm --prefix frontend ci && npm --prefix frontend run build
uv run tracepost --db demo.sqlite demo      # synthetic data, clearly marked [DEMO]
uv run tracepost --db demo.sqlite serve     # http://127.0.0.1:8765
uv run tracepost --db demo.sqlite list --platform xiaohongshu
```

Without `--db`, data lives in your user data directory (`%LOCALAPPDATA%\tracepost` on Windows), never in the repository.

## Use from an AI agent (MCP)

```json
{
  "mcpServers": {
    "tracepost": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/tracepost", "tracepost", "mcp"]
    }
  }
}
```

Tools: `status` and `list_contents`. Both are read-only, read only the local database, and return structured JSON with `schema_version`.

## Architecture

```text
platform adapters (planned) → sync runs → SQLite snapshots → shared queries → Web / CLI / MCP
```

A local modular monolith: Python, FastAPI, SQLite, Playwright and the MCP Python SDK. The React + TypeScript dashboard is prebuilt and served by the Python app. Why this shape: [architecture research](docs/research/2026-11-03-creator-hub-architecture.md) (Chinese).

## Responsible use

tracepost is meant for reading **your own** account data on your own machine. It does not bypass logins, captchas or rate limits, does not replay signed private APIs, and stops when the platform asks for human action. Automated access may still conflict with a platform's terms and may put your account at risk. You decide whether to use it. This project is not affiliated with Douyin, ByteDance, Xiaohongshu or any other platform.

## Development

```bash
uv run pytest -q
npm --prefix frontend run dev    # Vite dev server proxies /api to 127.0.0.1:8765
npm --prefix frontend run lint
```

Contributor and agent conventions: [AGENTS.md](AGENTS.md). Product spec: [docs/specs](docs/specs/2026-11-03-creator-hub.md).

## License

[MIT](LICENSE). Third-party code notices: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

---

## 中文说明

tracepost 在本机保存**你自己**在抖音、小红书发布内容的表现数据，并按时间留存快照。你可以在本地看板查看，也可以通过 CLI 导出 JSON，还可以通过 MCP 交给 AI Agent 分析。

- **当前状态**：项目还只是骨架。数据模型、看板、CLI 和 MCP 已经可以用合成 demo 数据运行，平台采集尚未实现。
- **原则**：缺失的指标记为 null 并注明原因，真实的 0 保持为 0；每个数字都带观测时间和来源；跨平台关联只由用户显式指定；查询工具只读。
- **风险**：本工具只读取本人数据，不绕过登录、验证码或风控。即便如此，自动化访问仍可能违反平台条款，带来账号风险，是否使用由你自行判断。
- 需求规格见 [docs/specs](docs/specs/2026-11-03-creator-hub.md)，进度见 [v0.1 计划](docs/plans/2026-11-03-v0.1.md)。
