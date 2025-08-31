"""
Task Orchestrator for smart progress evaluation and execution management.
Simple batch processing implementation that inherits from BaseOrchestrator.
"""

from typing import Dict, Any, List
from .base_orchestrator import BaseOrchestrator
from ..llm_client import LLMClient
from ..mcp_client import MCPClient


class TaskOrchestrator(BaseOrchestrator):
    """Simple orchestrator for batch task execution without interruption support."""

    def __init__(self, llm_client: LLMClient, mcp_client: MCPClient):
        super().__init__(llm_client, mcp_client)

    async def execute_task(self, user_request: str, max_iterations: int = 25) -> str:
        """
        Execute a complex task with smart orchestration.
        LLM client handles automatic tool calling, orchestrator manages iterations.

        Args:
            user_request: The user's task request
            max_iterations: Maximum number of iterations

        Returns:
            Final result or status
        """
        # Common preparation
        tool_names, openai_tools = await self._prepare_task_execution(user_request)

        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            
            # Execute iteration using base class method
            result = await self._execute_iteration(
                iteration, user_request, tool_names, openai_tools
            )

            # Check for completion or interruption
            if result.get("_completed"):
                return result["accomplished"]
            elif result.get("_interrupted"):
                return f"Task interrupted at {result['progress_percentage']}% completion: {result['accomplished']}"

        # Handle max iterations
        final_eval = await self.evaluate_progress(user_request, tool_names)
        return self._handle_max_iterations(max_iterations, final_eval)