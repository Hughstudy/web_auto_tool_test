"""
Instruction handler for terminal commands and help text.
Handles all command processing and instruction display logic isolated from interaction.py
"""

from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from src.resource_manager import ResourceManager


class Instruction:
    """Handles all instruction display and command processing for terminal interface."""
    
    def __init__(self, console: Console):
        self.console = console
    
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
    
    async def process_command(self, command_str: str, resource_manager: 'ResourceManager') -> bool:
        """
        Process a command string and execute the appropriate action.
        Returns True if the command was processed, False if it should exit.
        """
        if not command_str.startswith("/"):
            return True
            
        parts = command_str.split(" ", 1)
        command = parts[0].lower()
        
        if command == "/quit":
            self.console.print("[yellow]👋 Goodbye![/yellow]")
            return False
            
        elif command == "/model":
            if len(parts) > 1:
                # Switch model
                model_name = parts[1].strip()
                await self._handle_model_switch(model_name, resource_manager)
            else:
                # List models from OpenAI API
                await self._handle_list_models(resource_manager)
                
        elif command == "/clear":
            self._handle_clear_history(resource_manager)
            
        else:
            self.console.print(f"[red]❌ Unknown command: {command}[/red]")
            self.console.print("[dim]Available: /model, /clear, /quit[/dim]")
        
        return True
    
    async def _handle_list_models(self, resource_manager: 'ResourceManager'):
        """Handle listing models from OpenAI API."""
        models = await resource_manager.list_available_models()
        
        if not models:
            return
            
        table = Table(title="OpenAI API Models")
        table.add_column("Model ID", style="cyan")
        table.add_column("Owner", style="green")
        table.add_column("Status", style="yellow")
        
        for model in models:
            status = "✓ Current" if model["id"] == resource_manager.current_model else ""
            table.add_row(model["id"], model.get("owned_by", "N/A"), status)
            
        self.console.print(table)
    
    async def _handle_model_switch(self, model_name: str, resource_manager: 'ResourceManager'):
        """Handle switching to a different model."""
        resource_manager.switch_model(model_name)
    
    def _handle_clear_history(self, resource_manager: 'ResourceManager'):
        """Handle clearing conversation history."""
        resource_manager.clear_history()
    
    def display_model_info(self, current_model: str):
        """Display current model information."""
        self.console.print(f"\n[bold green]Current Model:[/bold green] {current_model}")