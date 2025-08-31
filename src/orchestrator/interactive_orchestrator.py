"""
Interactive Task Orchestrator with interrupt support and enhanced model management.
Interactive implementation that inherits from BaseOrchestrator with cancellation support.
"""

import asyncio
from typing import Dict, Any, List, Callable
from .base_orchestrator import BaseOrchestrator
from ..llm_client import LLMClient
from ..mcp_client import MCPClient


class InteractiveOrchestrator(BaseOrchestrator):
    """Enhanced orchestrator with interrupt support for interactive terminal use."""

    def __init__(self, llm_client: LLMClient, mcp_client: MCPClient):
        super().__init__(llm_client, mcp_client)

    async def execute_task(self, user_request: str, max_iterations: int = 25) -> str:
        """
        Execute a complex task with smart orchestration (non-interactive version).
        
        Args:
            user_request: The user's task request
            max_iterations: Maximum number of iterations

        Returns:
            Final result or status
        """
        # Delegate to the interactive version without interrupt callback
        return await self.execute_task_with_interrupt(user_request, None, max_iterations)

    async def execute_task_with_interrupt(
        self, user_request: str, should_stop: Callable[[], bool], max_iterations: int = 25
    ) -> str:
        """
        Execute a complex task with interrupt support.
        
        Args:
            user_request: The user's task request
            should_stop: Function that returns True when task should be interrupted
            max_iterations: Maximum number of iterations
            
        Returns:
            Final result or status
        """
        print(f"🎯 Starting interruptible task execution: {user_request}")

        # Common preparation
        tool_names, openai_tools = await self._prepare_task_execution(user_request)

        iteration = 0
        while iteration < max_iterations:
            iteration += 1

            try:
                # Execute iteration with interrupt support
                result = await self._execute_iteration(
                    iteration, user_request, tool_names, openai_tools, should_stop
                )

                # Check for completion or interruption
                if result.get("_completed"):
                    return result["accomplished"]
                elif result.get("_interrupted"):
                    return f"Task interrupted at {result['progress_percentage']}% completion: {result['accomplished']}"

                # Add a small delay to allow interrupt signals to be processed
                await asyncio.sleep(0.1)
                
            except asyncio.CancelledError:
                print("🛑 Task execution cancelled")
                final_eval = await self.evaluate_progress(user_request, tool_names)
                return f"Task cancelled at {final_eval['progress_percentage']}% completion: {final_eval['accomplished']}"

        # Handle max iterations
        final_eval = await self.evaluate_progress(user_request, tool_names)
        return self._handle_max_iterations(max_iterations, final_eval)