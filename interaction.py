"""
Smart Terminal Interface for Task Orchestration System.
Supports model switching, interactive prompts, ESC interruption, and command handling.
"""

import asyncio
import signal
from typing import Optional
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from src.llm_client import LLMClient
from src.mcp_client import MCPClient
from src.orchestrator import InteractiveOrchestrator


class TerminalInterface:
    """Smart terminal interface for interactive task orchestration."""
    
    
    def __init__(self):
        self.console = Console()
        self.current_model = "google/gemini-2.5-flash-lite"
        self.llm_client: Optional[LLMClient] = None
        self.mcp_client: Optional[MCPClient] = None
        self.orchestrator: Optional[InteractiveOrchestrator] = None
        self.task_running = False
        self.stop_task = False
        self.current_task: Optional[asyncio.Task] = None
        
    def display_welcome(self):
        """Display welcome message and instructions."""
        welcome_text = Text()
        welcome_text.append("🤖 Smart Task Orchestration Terminal\n\n", style="bold blue")
        welcome_text.append("Available Commands:\n", style="bold")
        welcome_text.append("/model          - List models from OpenAI API\n", style="green")
        welcome_text.append("/model <name>   - Switch to a different model\n", style="green")
        welcome_text.append("/clear          - Clear conversation history\n", style="green")
        welcome_text.append("/quit           - Exit the program\n", style="green")
        welcome_text.append("ESC/Ctrl+C      - Stop current task execution\n", style="yellow")
        welcome_text.append("\nType your task or use commands to get started!\n", style="dim")
        
        panel = Panel(welcome_text, title="Welcome", border_style="blue")
        self.console.print(panel)
        
    def display_model_info(self):
        """Display current model information."""
        self.console.print(f"\n[bold green]Current Model:[/bold green] {self.current_model}")
        
    async def list_models(self):
        """Display models available from OpenAI API."""
        await self.list_openai_models()
        
    async def list_openai_models(self):
        """Display models available from OpenAI API."""
        if not self.llm_client:
            self.console.print("[red]❌ LLM client not initialized[/red]")
            return
            
        self.console.print("[yellow]🔍 Fetching models from OpenAI API...[/yellow]")
        models = await self.llm_client.list_available_models()
        
        if not models:
            self.console.print("[red]❌ No models found or API error[/red]")
            return
            
        table = Table(title="OpenAI API Models")
        table.add_column("Model ID", style="cyan")
        table.add_column("Owner", style="green")
        table.add_column("Status", style="yellow")
        
        for model in models:
            status = "✓ Current" if model["id"] == self.current_model else ""
            table.add_row(model["id"], model.get("owned_by", "N/A"), status)
            
        self.console.print(table)
        
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
            
    async def initialize_clients(self):
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
            
    def setup_interrupt_handler(self):
        """Setup keyboard interrupt handling for ESC key."""
        def signal_handler(signum, frame):
            if self.task_running and self.current_task:
                self.console.print("\n[yellow]⏹️  Task interrupted by user[/yellow]")
                self.stop_task = True
                # Cancel the running task
                if not self.current_task.done():
                    self.current_task.cancel()
                
        signal.signal(signal.SIGINT, signal_handler)
        
    async def execute_task_with_interrupt(self, user_request: str) -> str:
        """Execute task with ability to interrupt via ESC/Ctrl+C."""
        self.task_running = True
        self.stop_task = False
        
        try:
            # Create a cancellable task
            task = asyncio.create_task(
                self.orchestrator.execute_task_with_interrupt(
                    user_request, lambda: self.stop_task
                )
            )
            self.current_task = task
            
            result = await task
            return result
            
        except asyncio.CancelledError:
            return "Task was interrupted by user"
        except Exception as e:
            if self.stop_task:
                return "Task was interrupted by user"
            raise e
        finally:
            self.task_running = False
            self.stop_task = False
            self.current_task = None
            
    async def run(self):
        """Main terminal interaction loop."""
        self.display_welcome()
        self.setup_interrupt_handler()
        
        # Initialize clients
        if not await self.initialize_clients():
            return
            
        self.display_model_info()
        
        while True:
            try:
                # Get user input
                user_input = Prompt.ask("\n[bold cyan]>>[/bold cyan]", console=self.console).strip()
                
                if not user_input:
                    continue
                    
                # Handle commands
                if user_input.startswith("/"):
                    parts = user_input.split(" ", 1)
                    command = parts[0].lower()
                    
                    if command == "/quit":
                        self.console.print("[yellow]👋 Goodbye![/yellow]")
                        break
                        
                    elif command == "/model":
                        if len(parts) > 1:
                            # Switch model
                            model_name = parts[1].strip()
                            self.switch_model(model_name)
                        else:
                            # List models from OpenAI API
                            await self.list_models()
                            
                    elif command == "/clear":
                        self.clear_history()
                        
                    else:
                        self.console.print(f"[red]❌ Unknown command: {command}[/red]")
                        self.console.print("[dim]Available: /model, /clear, /quit[/dim]")
                        
                else:
                    # Check if there's a running task and interrupt it
                    if self.task_running and self.current_task:
                        self.console.print("[yellow]⏹️  Interrupting current task to start new one...[/yellow]")
                        self.stop_task = True
                        if not self.current_task.done():
                            self.current_task.cancel()
                        # Wait briefly for the task to be cancelled
                        try:
                            await asyncio.wait_for(self.current_task, timeout=2.0)
                        except (asyncio.CancelledError, asyncio.TimeoutError):
                            pass
                        
                        # Reset state
                        self.task_running = False
                        self.stop_task = False
                        self.current_task = None
                        
                        # Clear conversation history for fresh start
                        if self.orchestrator:
                            self.orchestrator.messages.clear()
                            self.console.print("[green]✅ Conversation reset for new task[/green]")
                    
                    # Execute user task
                    if not self.orchestrator:
                        self.console.print("[red]❌ System not initialized[/red]")
                        continue
                        
                    self.console.print(f"\n[bold blue]🎯 Starting task:[/bold blue] {user_input}")
                    self.console.print("[dim](Press Ctrl+C to interrupt)[/dim]")
                    
                    try:
                        result = await self.execute_task_with_interrupt(user_input)
                        
                        if not self.stop_task:
                            self.console.print(f"\n[bold green]🎉 Task completed:[/bold green]")
                            self.console.print(Panel(result, border_style="green"))
                        else:
                            self.console.print("\n[yellow]⏹️  Task was interrupted[/yellow]")
                            
                    except KeyboardInterrupt:
                        self.console.print("\n[yellow]⏹️  Task interrupted[/yellow]")
                    except Exception as e:
                        self.console.print(f"\n[red]❌ Task failed: {e}[/red]")
                        
            except KeyboardInterrupt:
                if self.task_running:
                    self.console.print("\n[yellow]⏹️  Task interrupted[/yellow]")
                    self.stop_task = True
                else:
                    self.console.print("\n[yellow]👋 Use /quit to exit[/yellow]")
            except EOFError:
                break
                
        # Cleanup
        if self.mcp_client:
            await self.mcp_client.__aexit__(None, None, None)


async def main():
    """Main entry point for the terminal interface."""
    terminal = TerminalInterface()
    await terminal.run()


if __name__ == "__main__":
    asyncio.run(main())