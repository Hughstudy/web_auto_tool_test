"""
Resource Manager for handling LLM client, MCP client, and orchestrator.
Centralizes resource management and initialization logic.
"""

from typing import Optional
from rich.console import Console
from src.llm_client import LLMClient
from src.mcp_client import MCPClient
from src.orchestrator import InteractiveOrchestrator


class ResourceManager:
    """Manages LLM client, MCP client, and orchestrator resources."""
    
    def __init__(self, console: Console, initial_model: str = "google/gemini-2.5-flash-lite"):
        self.console = console
        self.current_model = initial_model
        self.llm_client: Optional[LLMClient] = None
        self.mcp_client: Optional[MCPClient] = None
        self.orchestrator: Optional[InteractiveOrchestrator] = None
        
    async def initialize_clients(self) -> bool:
        """Initialize LLM and MCP clients."""
        try:
            self.llm_client = LLMClient(self.current_model)
            self.mcp_client = MCPClient("http://localhost:8931/mcp")
            await self.mcp_client.__aenter__()
            self.orchestrator = InteractiveOrchestrator(self.llm_client, self.mcp_client)
            self.console.print("[green]✅ Connected to MCP server[/green]")
            return True
        except Exception as e:
            self.console.print(f"[red]❌ Failed to initialize: {e}[/red]")
            return False
    
    async def ensure_mcp_connection(self) -> bool:
        """Ensure MCP connection is active, reconnect if needed."""
        if not self.mcp_client:
            self.console.print("[yellow]⚠️  No MCP client, initializing...[/yellow]")
            return await self.initialize_clients()
            
        try:
            # Test the connection
            ping_result = await self.mcp_client.ping()
            if not ping_result:
                self.console.print("[yellow]⚠️  MCP connection lost, reconnecting...[/yellow]")
                # Close old connection
                try:
                    await self.mcp_client.__aexit__(None, None, None)
                except:
                    pass
                # Reinitialize
                return await self.initialize_clients()
            return True
        except Exception as e:
            self.console.print(f"[yellow]⚠️  MCP connection error: {e}, reconnecting...[/yellow]")
            try:
                await self.mcp_client.__aexit__(None, None, None)
            except:
                pass
            return await self.initialize_clients()
    
    async def recreate_mcp_connection_preserving_memory(self):
        """Recreate MCP connection while preserving orchestrator and conversation memory."""
        # Save the current conversation memory
        saved_messages = None
        if self.orchestrator and self.orchestrator.messages:
            saved_messages = self.orchestrator.messages
            
        # Close old MCP connection cleanly
        if self.mcp_client:
            try:
                await self.mcp_client.__aexit__(None, None, None)
            except:
                pass
                
        # Create new MCP connection
        try:
            self.mcp_client = MCPClient("http://localhost:8931/mcp")
            await self.mcp_client.__aenter__()
            
            # Recreate orchestrator with the same LLM client but new MCP client
            if self.orchestrator:
                # Preserve the existing LLM client
                old_llm_client = self.orchestrator.llm_client
                self.orchestrator = InteractiveOrchestrator(old_llm_client, self.mcp_client)
                
                # Restore conversation memory
                if saved_messages:
                    self.orchestrator.messages = saved_messages
                    self.console.print("[green]✅ Session reconnected with conversation memory preserved[/green]")
                else:
                    self.console.print("[green]✅ Session reconnected[/green]")
            else:
                # Fallback to full initialization if orchestrator was somehow lost
                await self.initialize_clients()
                
        except Exception as e:
            self.console.print(f"[red]❌ Failed to recreate MCP connection: {e}[/red]")
    
    def switch_model(self, model_name: str) -> bool:
        """Switch to a different model."""
        if model_name == self.current_model:
            self.console.print(f"[yellow]Already using {model_name}[/yellow]")
            return True
            
        try:
            self.current_model = model_name
            self.llm_client = LLMClient(self.current_model)
            if self.orchestrator:
                self.orchestrator.llm_client = self.llm_client
                # Update tool executor
                self.orchestrator.llm_client.set_tool_executor(self.mcp_client.call_tool)
            self.console.print(f"[green]✅ Switched to {model_name}[/green]")
            return True
        except Exception as e:
            self.console.print(f"[red]❌ Failed to switch model: {e}[/red]")
            return False
    
    def clear_history(self):
        """Clear conversation history."""
        if self.orchestrator:
            self.orchestrator.messages.clear()
            self.console.print("[green]✅ Conversation history cleared[/green]")
        else:
            self.console.print("[yellow]No active session to clear[/yellow]")
    
    async def list_available_models(self):
        """List available models from LLM client."""
        if not self.llm_client:
            self.console.print("[red]❌ LLM client not initialized[/red]")
            return None
            
        self.console.print("[yellow]🔍 Fetching models from OpenAI API...[/yellow]")
        models = await self.llm_client.list_available_models()
        
        if not models:
            self.console.print("[red]❌ No models found or API error[/red]")
            return None
            
        return models
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.mcp_client:
            await self.mcp_client.__aexit__(None, None, None)