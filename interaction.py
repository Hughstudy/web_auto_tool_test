"""
Smart Terminal Interface for Task Orchestration System.
Supports model switching, interactive prompts, ESC interruption, and command handling.
"""

import asyncio
import signal
from typing import Optional
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from src.resource_manager import ResourceManager
from src.instruction import Instruction


class TerminalInterface:
    """Smart terminal interface for interactive task orchestration."""
    
    
    def __init__(self):
        self.console = Console()
        self.task_running = False
        self.stop_task = False
        self.current_task: Optional[asyncio.Task] = None
        self.resource_manager = ResourceManager(self.console)
        self.instruction = Instruction(self.console)
        
    def display_welcome(self):
        """Display welcome message and instructions."""
        self.instruction.display_welcome()
        
    def display_model_info(self):
        """Display current model information."""
        self.instruction.display_model_info(self.resource_manager.current_model)
            
    def setup_interrupt_handler(self):
        """Setup keyboard interrupt handling for ESC key."""
        def signal_handler(_signum, _frame):
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
                self.resource_manager.orchestrator.execute_task_with_interrupt(
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
        if not await self.resource_manager.initialize_clients():
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
                    should_continue = await self.instruction.process_command(user_input, self.resource_manager)
                    if not should_continue:
                        break
                        
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
                        if self.resource_manager.orchestrator:
                            self.resource_manager.orchestrator.messages.clear()
                            self.console.print("[green]✅ Conversation reset for new task[/green]")
                    
                    # Execute user task
                    if not self.resource_manager.orchestrator:
                        self.console.print("[red]❌ System not initialized[/red]")
                        continue
                    
                    # Ensure MCP connection is active before starting task
                    if not await self.resource_manager.ensure_mcp_connection():
                        self.console.print("[red]❌ Cannot establish MCP connection[/red]")
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
                        error_msg = str(e)
                        self.console.print(f"\n[red]❌ Task failed: {error_msg}[/red]")
                        
                        # Check if this is a session termination error
                        if "session" in error_msg.lower() or "terminated" in error_msg.lower():
                            self.console.print("[yellow]⚠️  Browser session was terminated. This is normal after task completion.[/yellow]")
                            self.console.print("[yellow]💡 Reconnecting while preserving conversation memory...[/yellow]")
                            # Only recreate MCP connection, preserve orchestrator and its memory
                            await self.resource_manager.recreate_mcp_connection_preserving_memory()
                        else:
                            # Check if MCP connection is still alive for other errors
                            if self.resource_manager.mcp_client:
                                try:
                                    ping_result = await self.resource_manager.mcp_client.ping()
                                    if not ping_result:
                                        self.console.print("[yellow]⚠️  MCP server connection lost. Will reconnect on next task.[/yellow]")
                                    else:
                                        self.console.print("[green]✅ MCP server connection is still active[/green]")
                                except Exception as ping_error:
                                    self.console.print(f"[yellow]⚠️  Cannot ping MCP server: {ping_error}[/yellow]")
                        
            except KeyboardInterrupt:
                if self.task_running:
                    self.console.print("\n[yellow]⏹️  Task interrupted[/yellow]")
                    self.stop_task = True
                else:
                    self.console.print("\n[yellow]👋 Use /quit to exit[/yellow]")
            except EOFError:
                break
                
        # Cleanup
        await self.resource_manager.cleanup()


async def main():
    """Main entry point for the terminal interface."""
    terminal = TerminalInterface()
    await terminal.run()


if __name__ == "__main__":
    asyncio.run(main())