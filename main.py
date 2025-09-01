"""
Smart demo: Clean architecture with TaskOrchestrator managing LLM and MCP clients.
Architecture: main -> TaskOrchestrator -> LLMClient + MCPClient
"""

import asyncio
from rich.console import Console
from src.resource_manager import ResourceManager
from src.orchestrator import TaskOrchestrator


async def main():
    """Simple demo with clean architecture using ResourceManager."""
    console = Console()
    console.print("🤖 Smart Task Orchestration Demo", style="bold blue")

    try:
        # Initialize resource manager
        resource_manager = ResourceManager(console, "google/gemini-2.5-flash-lite")
        
        # Initialize clients
        if not await resource_manager.initialize_clients():
            console.print("[red]❌ Failed to initialize clients[/red]")
            return

        # Create orchestrator with clients from resource manager
        orchestrator = TaskOrchestrator(resource_manager.llm_client, resource_manager.mcp_client)

        # User's task request - orchestrator handles all the complexity
        user_request = """
        1. Open google.com and search for the latest earnings call transcript for Nvidia
        2. Try to find the latest earnings call transcript from Yahoo Finance
        3. Read the earnings call transcript
        4. Give me a summary of the earnings call transcript QA session
        """

        # Execute task with smart orchestration
        result = await orchestrator.execute_task(user_request)

        console.print(f"\n🎉 Final Result: {result}", style="bold green")

        # Cleanup
        await resource_manager.cleanup()

    except Exception as e:
        console.print(f"❌ Demo failed: {e}", style="red")
        raise e

if __name__ == "__main__":
    asyncio.run(main())
