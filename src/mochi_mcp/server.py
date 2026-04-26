import os
from fastmcp import FastMCP
from mochi_mcp.client import MochiClient
from mochi_mcp.tools import register_tools


def main() -> None:
    api_key = os.environ.get("MOCHI_API_KEY")
    if not api_key:
        raise ValueError("MOCHI_API_KEY environment variable is required")

    client = MochiClient(api_key=api_key)
    mcp = FastMCP("mochi-mcp")
    register_tools(mcp, client)
    mcp.run()


if __name__ == "__main__":
    main()
