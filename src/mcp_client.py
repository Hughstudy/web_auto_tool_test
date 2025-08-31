"""
MCP Client for connecting to Model Context Protocol servers using FastMCP.
"""

from typing import Dict, Any, List
from fastmcp import Client


class MCPClient:
    """MCP Client wrapper for FastMCP."""

    def __init__(self, server_url: str):
        """
        Initialize MCP client.

        Args:
            server_url: URL of the MCP server
        """
        self.server_url = server_url
        self.client = Client(server_url)

    async def __aenter__(self):
        """Async context manager entry."""
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def ping(self) -> bool:
        """Test server connectivity."""
        try:
            await self.client.ping()
            return True
        except Exception:
            return False

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools."""
        return await self.client.list_tools()

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool with arguments."""
        try:
            return await self.client.call_tool(name, arguments)
        except Exception as e:
            # Add more specific error information
            error_msg = str(e)
            if "session" in error_msg.lower() or "terminated" in error_msg.lower():
                raise Exception(f"Browser session terminated: {error_msg}")
            else:
                raise Exception(f"Tool call failed: {error_msg}")
