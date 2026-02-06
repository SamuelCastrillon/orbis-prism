# Entrypoints: CLI and MCP server (use application + infrastructure).

from .cli import main
from .mcp_server import run

__all__ = ["main", "run"]