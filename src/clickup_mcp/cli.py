"""CLI entry point for ClickUp MCP server."""

import asyncio


def main():
    """Run the ClickUp MCP server."""
    from .server import main as server_main

    asyncio.run(server_main())


if __name__ == "__main__":
    main()
