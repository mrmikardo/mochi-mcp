# mochi-mcp Design Spec

**Date:** 2026-04-26  
**Status:** Approved

## Overview

A lightweight MCP server that wraps the [Mochi Cards REST API](https://mochi.cards/docs/api/), providing read access to decks and cards. Built with FastMCP and packaged with `uv` for distribution via `uvx`.

## Goals

- Expose Mochi deck and card data as MCP tools consumable by LLMs (e.g. Claude)
- Auto-paginate all list endpoints so tools always return complete results
- Be publishable to PyPI as `mochi-mcp`

## Out of Scope

- Write operations (create/update/delete decks or cards)
- MCP Resources or Prompts
- Caching or rate limiting

---

## Package Structure

```
mochi-mcp/
├── pyproject.toml
├── README.md
├── src/
│   └── mochi_mcp/
│       ├── __init__.py
│       ├── client.py       # httpx-based Mochi API client
│       ├── tools.py        # FastMCP tool definitions
│       └── server.py       # FastMCP app + entry point
└── tests/
    ├── test_client.py
    └── test_tools.py
```

`src/` layout is used for PyPI compatibility. The `mochi-mcp` console script entry point in `pyproject.toml` points to `mochi_mcp.server:main`.

**Dependencies:** `fastmcp`, `httpx`  
**Dev dependencies:** `pytest`

---

## MCP Tools

All tools are read-only. No write operations are exposed.

| Tool | Signature | Description |
|------|-----------|-------------|
| `list_decks` | `() → list[dict]` | Returns all decks (auto-paginates) |
| `get_deck` | `(deck_id: str) → dict` | Returns a single deck by ID |
| `list_cards` | `(deck_id: str \| None = None) → list[dict]` | Returns all cards, optionally filtered by deck (auto-paginates) |
| `get_card` | `(card_id: str) → dict` | Returns a single card by ID |

Pagination is handled entirely within `client.py`. The Mochi `bookmark` cursor is never exposed to the MCP layer or the LLM.

---

## Components

### `client.py` — Mochi API Client

- Instantiated with the API key at startup
- Uses `httpx.Client` (synchronous, matching FastMCP's default sync tool model)
- Auth: HTTP Basic with API key as username, empty password
- Base URL: `https://app.mochi.cards/api/`
- Exposes four methods mirroring the tools: `list_decks()`, `get_deck(id)`, `list_cards(deck_id=None)`, `get_card(id)`
- `list_decks` and `list_cards` loop internally until `bookmark` is exhausted, accumulating results into a flat list

### `tools.py` — Tool Definitions

- Instantiates a module-level `MochiClient` from `MOCHI_API_KEY` at import time
- Exposes a `register_tools(mcp: FastMCP)` function that registers the four tools on the given app instance using `@mcp.tool` decorators
- Each tool delegates directly to the corresponding client method — no business logic here
- This pattern avoids circular imports: `tools.py` never imports from `server.py`

### `server.py` — Entry Point

- Creates the `FastMCP` app instance: `mcp = FastMCP("mochi-mcp")`
- Calls `register_tools(mcp)` from `tools.py` to attach all tools
- Defines `main()` which calls `mcp.run()`
- `pyproject.toml` points the `mochi-mcp` script at `mochi_mcp.server:main`

---

## Auth & Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `MOCHI_API_KEY` | Yes | Mochi API key, used as HTTP Basic Auth username |

Read via `os.environ` in `client.py`. If absent, a `ValueError` is raised at import time with a clear message. No config file — environment variable only.

**Claude Desktop configuration:**

```json
{
  "mcpServers": {
    "mochi": {
      "command": "uvx",
      "args": ["mochi-mcp"],
      "env": { "MOCHI_API_KEY": "your-key-here" }
    }
  }
}
```

---

## Error Handling

- HTTP errors from `httpx` are caught in `client.py` and re-raised as `Exception` with a human-readable message: `"Mochi API returned {status}: {detail}"`
- FastMCP surfaces these as tool errors to the LLM
- No retries — fail fast on API errors
- Missing API key fails at startup, not at first tool call

---

## Testing

- Framework: `pytest`
- Transport: `httpx.MockTransport` (no real API calls, no mocking libraries)
- `test_client.py`: covers pagination logic (multiple bookmark pages → flat list), auth header is set correctly, HTTP errors produce readable messages
- `test_tools.py`: covers tool signatures, list tools return flat lists, `deck_id` filter is passed through correctly
