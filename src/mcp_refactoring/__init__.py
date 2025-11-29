"""MCP server exposing Martin Fowler's refactoring catalog to LLMs."""

from mcp_refactoring.server import mcp, main

__version__ = "0.1.1"
__all__ = ["mcp", "main"]
