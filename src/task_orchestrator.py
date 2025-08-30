"""
Task Orchestrator for smart progress evaluation and execution management.
"""

from email import message
import json
from typing import Dict, Any, List
from .llm_client import LLMClient
from .mcp_client import MCPClient
from .message_system import MessageSystem
from src import message_system


class TaskOrchestrator:
    """Smart orchestrator for evaluating task progress and managing execution."""

    def __init__(self, llm_client: LLMClient, mcp_client: MCPClient):
        self.llm_client = llm_client
        self.mcp_client = mcp_client
        self.messages = MessageSystem()

    async def evaluate_progress(
        self,
        user_request: str,
        available_tools: List[str],
    ) -> Dict[str, Any]:
        """
        Evaluate current task progress and suggest next steps.

        Args:
            user_request: Original user request
            available_tools: List of available tool names

        Returns:
            Evaluation with progress assessment and next step suggestions
        """
        # Create evaluation prompt
        tools_list = ", ".join(available_tools)  # Show first 10 tools

        evaluation_prompt = f"""
You are a task progress evaluator. Analyze the current state and provide guidance.

ORIGINAL USER REQUEST: {user_request}

AVAILABLE BROWSER TOOLS: {tools_list}

CONVERSATION HISTORY:
{self.messages.get_conversation_summary()}

Please evaluate:
1. What has been accomplished so far?
2. What percentage complete is the task (0-100%)?
3. What specific step should happen next?
4. Which tool should be used for the next step?
5. Is the task complete? (yes/no)

Respond in JSON format:
{{
    "accomplished": "description of what's done",
    "progress_percentage": 0-100,
    "next_step": "specific next action needed",
    "suggested_tool": "tool_name or null",
    "is_complete": true/false,
    "reasoning": "explanation of assessment"
}}

This is an example response:
{{
    "accomplished": "I have searched for the weather in Shanghai",
    "progress_percentage": 50,
    "next_step": "Open the weather website",
    "suggested_tool": "browser_tools.search",
    "is_complete": false,
    "reasoning": "I have searched for the weather in Shanghai"
}}

This output should not have something like ```json and ``` in the response.
"""

        messages = [{"role": "user", "content": evaluation_prompt}]

        # Try with JSON format first, fallback to regular if not supported
        try:
            response = await self.llm_client.chat_completion(
                messages=messages, response_format={"type": "json_object"}, tool_choice="none"
            )
        except Exception as e:
            print(f"⚠️  JSON format not supported ({e}), using regular format...")
            response = await self.llm_client.chat_completion(messages=messages, tool_choice="none")

        content = response.choices[0].message.content
        print(f"🔍 Evaluation response: {content[:200]}...")  # Debug output

        if not content or content.strip() == "":
            return {
                "accomplished": "No evaluation content received",
                "progress_percentage": 10,  # Give some progress to avoid getting stuck
                "next_step": "Continue with original request",
                "suggested_tool": None,
                "is_complete": False,
                "reasoning": "Empty evaluation response",
            }

        try:
            # Try to parse as JSON
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON parsing failed: {e}")

            # Fallback: extract basic info from text response
            progress = 20  # Default progress
            is_complete = False

            # Simple text parsing as fallback
            if "complete" in content.lower() or "done" in content.lower():
                progress = 100
                is_complete = True
            elif "%" in content:
                # Try to extract percentage
                import re

                match = re.search(r"(\d+)%", content)
                if match:
                    progress = int(match.group(1))

            return {
                "accomplished": (
                    content[:100] + "..." if len(content) > 100 else content
                ),
                "progress_percentage": progress,
                "next_step": "Continue with task execution",
                "suggested_tool": None,
                "is_complete": is_complete,
                "reasoning": f"Parsed from text response (JSON failed: {str(e)})",
            }

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
        print(f"🎯 Starting task execution: {user_request}")

        # Setup tool executor for LLM client
        self.llm_client.set_tool_executor(self.mcp_client.call_tool)

        # Get available tools
        mcp_tools = await self.mcp_client.list_tools()
        tool_names = [tool.name for tool in mcp_tools]
        print(f"🔧 Connected to MCP with {len(tool_names)} tools available")

        # Convert tools to OpenAI format
        openai_tools = []
        for tool in mcp_tools:
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": getattr(tool, "description", ""),
                    "parameters": getattr(
                        tool, "inputSchema", {"type": "object", "properties": {}}
                    ),
                },
            }
            openai_tools.append(openai_tool)

        # Initialize conversation with MessageSystem
        self.messages.clear()
        self.messages.add_user_message(
            f"""
Task: {user_request}

You have access to browser automation tools. Execute this task step by step.
Available tools include: {', '.join(tool_names)}

Please start by taking the first necessary action to complete this task.
"""
        )

        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            print(f"\n--- Iteration {iteration} ---")

            # Get orchestrator evaluation
            evaluation = await self.evaluate_progress(user_request, tool_names)

            print(
                f"📊 Progress: {evaluation['progress_percentage']}% - {evaluation['accomplished']}"
            )
            print(f"🤔 Next step: {evaluation['next_step']}")

            if evaluation["is_complete"]:
                print("✅ Task marked as complete by orchestrator!")
                return evaluation["accomplished"]

            self.messages.add_user_message(f"You should make your own decision, but you could use {evaluation["next_step"]} as a reference")
            # Use LLM client with automatic tool calling
            await self.llm_client.prompt_with_auto_tools(
                self.messages, tools=openai_tools
            )

        print(f"⚠️  Reached maximum iterations ({max_iterations})")
        final_eval = await self.evaluate_progress(user_request, tool_names)
        return f"Task partially completed ({final_eval['progress_percentage']}%): {final_eval['accomplished']}"
