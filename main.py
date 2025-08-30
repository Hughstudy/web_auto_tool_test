"""
Smart demo: Clean architecture with TaskOrchestrator managing LLM and MCP clients.
Architecture: main -> TaskOrchestrator -> LLMClient + MCPClient
"""

import asyncio
from src.llm_client import LLMClient
from src.mcp_client import MCPClient
from src.task_orchestrator import TaskOrchestrator


async def main():
    """Simple demo with clean architecture: main -> TaskOrchestrator -> clients."""
    print("🤖 Smart Task Orchestration Demo")

    try:
        # Create clean, focused clients
        llm_client = LLMClient()
        mcp_client = MCPClient("http://localhost:8931/mcp")

        # Use MCP client as context manager
        async with mcp_client:
            # Create orchestrator with both clients
            orchestrator = TaskOrchestrator(llm_client, mcp_client)

            # User's task request - orchestrator handles all the complexity
            user_request = """
            1. Open google.com and search for the latest earnings call transcript for Nvidia
            2. Try to find the latest earnings call transcript
            3. Read the earnings call transcript
            4. Give me a summary of the earnings call transcript QA session
            """

            # Execute task with smart orchestration
            result = await orchestrator.execute_task(user_request)

            print(f"\n🎉 Final Result: {result}")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        raise e

if __name__ == "__main__":
    asyncio.run(main())
