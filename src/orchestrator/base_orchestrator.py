"""
Base Orchestrator for smart progress evaluation and execution management.
Contains all common logic shared between different orchestrator implementations.
"""

import json
from typing import Dict, Any, List, Callable, Optional
from ..llm_client import LLMClient
from ..mcp_client import MCPClient
from ..message_system import MessageSystem


class BaseOrchestrator:
    """Base orchestrator with common functionality for task evaluation and execution."""

    def __init__(self, llm_client: LLMClient, mcp_client: MCPClient):
        self.llm_client = llm_client
        self.mcp_client = mcp_client
        self.messages = MessageSystem()
        self.token_threshold = 100000

    async def _auto_compact_if_needed(self) -> bool:
        """
        Automatically compact conversation if it gets too long.
        
        Returns:
            True if compaction was performed, False otherwise
        """
        estimated_tokens = self.messages.estimate_token_count()
        
        if estimated_tokens > self.token_threshold:
            print(f"🗜️  Auto-compacting conversation ({estimated_tokens} estimated tokens > {self.token_threshold} threshold)")
            
            try:
                # Compact the conversation
                compacted_messages = await self.messages.compact_conversation(self.llm_client, target_words=5000)
                
                # Replace current messages with compacted version
                self.messages = compacted_messages
                
                new_token_count = self.messages.estimate_token_count()
                print(f"✅ Conversation compacted: {estimated_tokens} → {new_token_count} estimated tokens")
                
                return True
                
            except Exception as e:
                print(f"❌ Failed to compact conversation: {e}")
                return False
        
        return False

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
        # Auto-compact if conversation is getting too long
        await self._auto_compact_if_needed()
        
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

    async def _prepare_task_execution(self, user_request: str):
        """
        Common preparation steps for task execution.
        
        Returns:
            Tuple of (tool_names, openai_tools)
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
        self.messages.set_last_request(user_request)
        self.messages.add_user_message(
            f"""
Task: {user_request}

You have access to browser automation tools. Execute this task step by step.
Available tools include: {', '.join(tool_names)}

Please start by taking the first necessary action to complete this task.
"""
        )

        return tool_names, openai_tools

    async def _execute_iteration(
        self, 
        iteration: int, 
        user_request: str, 
        tool_names: List[str], 
        openai_tools: List[Dict], 
        should_stop: Optional[Callable[[], bool]] = None
    ) -> Dict[str, Any]:
        """
        Execute a single iteration of the task orchestration loop.
        
        Args:
            iteration: Current iteration number
            user_request: Original user request
            tool_names: List of available tool names
            openai_tools: OpenAI-formatted tools
            should_stop: Optional callback to check if execution should stop
            
        Returns:
            Dictionary with evaluation results and completion status
        """
        print(f"\n--- Iteration {iteration} ---")

        # Check if user wants to stop (for interactive mode)
        if should_stop and should_stop():
            print("🛑 Task interrupted by user")
            final_eval = await self.evaluate_progress(user_request, tool_names)
            return {**final_eval, "_interrupted": True}

        # Get orchestrator evaluation
        evaluation = await self.evaluate_progress(user_request, tool_names)

        print(
            f"📊 Progress: {evaluation['progress_percentage']}% - {evaluation['accomplished']}"
        )
        print(f"🤔 Next step: {evaluation['next_step']}")

        if evaluation["is_complete"]:
            print("✅ Task marked as complete by orchestrator!")
            return {**evaluation, "_completed": True}

        # Check interrupt again before tool execution (for interactive mode)
        if should_stop and should_stop():
            print("🛑 Task interrupted by user")
            return {**evaluation, "_interrupted": True}

        self.messages.add_user_message(f"You should make your own decision without asking user's help, but you could use {evaluation['next_step']} as a reference")

        # Use LLM client with automatic tool calling
        await self.llm_client.prompt_with_auto_tools(
            self.messages, tools=openai_tools
        )

        return {**evaluation, "_continue": True}

    def _handle_max_iterations(self, max_iterations: int, final_eval: Dict[str, Any]) -> str:
        """Handle the case when maximum iterations are reached."""
        print(f"⚠️  Reached maximum iterations ({max_iterations})")
        return f"Task partially completed ({final_eval['progress_percentage']}%): {final_eval['accomplished']}"