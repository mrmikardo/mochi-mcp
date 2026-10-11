# mochi-mcp

MCP server for the [Mochi Cards](https://mochi.cards) API. Provides read access to your decks and cards.

## Tools

| Tool | Description |
|------|-------------|
| `list_decks` | List all your Mochi decks |
| `get_deck` | Get a single deck by ID |
| `list_cards` | List all cards (optionally filtered by `deck_id`) |
| `get_card` | Get a single card by ID |

## Setup

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mochi": {
      "command": "uvx",
      "args": ["mochi-mcp"],
      "env": { "MOCHI_API_KEY": "your-api-key-here" }
    }
  }
}
```

Your Mochi API key is in [Mochi Settings → API](https://app.mochi.cards/settings).

### Development

```bash
uv sync
MOCHI_API_KEY=your-key uv run mochi-mcp
```

### Dev with inspector

The [MCP inspector](https://github.com/modelcontextprotocol/inspector) is an extremely useful tool for local dev, as it
allows you to list and view the tools in a satisfying GUI. If you're
doing local dev work on this server, it's strongly recommended that you
use the inspector.

To run the inspector, you should do

```bash
cp mcp_debug_config.template.json mcp_debug_config.json

```

and then fill in the relevant environment variables (see above).

You can then run the inspector:

```bash
npx @modelcontextprotocol/inspector --config mcp_debug_config.json --server mochi-mcp
```

## Requirements

- Python 3.11+
- A [Mochi Cards](https://mochi.cards) account and API key
