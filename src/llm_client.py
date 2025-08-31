"""
LLM Client for OpenAI API integration with single-cycle tool calling automation.
OpenAI API fully supports tool calling (function calling) since GPT-3.5-turbo and GPT-4.
"""

import os
import json
from typing import Dict, Any, List, Callable, Awaitable
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()


class LLMClient:
    """LLM Client that handles one prompt cycle with automatic tool execution."""

    def __init__(self, model_name: str, api_key: str = None, base_url: str = None):
        """
        Initialize LLM client.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            base_url: OpenAI base URL (defaults to OPENAI_BASE_URL env var)
        """
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        base_url = base_url or os.getenv("OPENAI_BASE_URL")

        if not api_key:
            raise ValueError("OpenAI API key is required")

        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url

        self.client = AsyncOpenAI(**kwargs)
        self.model = model_name

        # Tool executor function - to be set by orchestrator
        self._tool_executor: Callable[[str, Dict[str, Any]], Awaitable[Any]] = None

    def set_tool_executor(
        self, executor: Callable[[str, Dict[str, Any]], Awaitable[Any]]
    ):
        """
        Set the tool executor function for automatic tool calling.

        Args:
            executor: Async function that takes (tool_name, tool_args) and returns result
        """
        self._tool_executor = executor

    async def _execute_tool_with_retries(self, message_system, tool_call, max_retries: int = 3) -> Dict[str, Any]:
        """
        Execute a tool with up to max_retries attempts. Adds tool result to message_system
        on success or after final failure.
        """
        tool_name = tool_call.function.name
        # Parse tool args safely
        try:
            tool_args = json.loads(tool_call.function.arguments) if getattr(tool_call.function, 'arguments', None) else {}
        except Exception as parse_err:
            print(f"❌ Tool args parse failed for {tool_name}: {parse_err}")
            return {
                "tool_name": tool_name,
                "tool_args": {},
                "result": f"Error: invalid tool arguments ({parse_err})",
                "success": False,
            }

        attempt = 0
        last_error = None
        while attempt < max_retries:
            attempt += 1
            try:
                print(f"⚡ Auto-executing: {tool_name}({list(tool_args.keys())}) attempt {attempt}/{max_retries}")
                result = await self._tool_executor(tool_name, tool_args)
                result_str = str(result)
                print(f"✅ Result: {tool_name} executed successfully")
                # Add tool result once on success
                message_system.add_tool_result(tool_call.id, result_str)
                return
            except Exception as e:
                last_error = e
                print(f"❌ Tool failed (attempt {attempt}/{max_retries}): {e}")

        # After all retries failed, record failure
        message_system.add_tool_result(tool_call.id, "Tool execution failed")
        return {
            "tool_name": tool_name,
            "tool_args": tool_args,
            "result": f"Error: {str(last_error)}",
            "success": False,
            "attempts": attempt,
        }

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        tools: List[Dict[str, Any]] = None,
        tool_choice: str = "auto",
        response_format: Dict[str, str] = None,
    ) -> Any:
        """
        Basic chat completion without tool execution.

        Args:
            messages: Chat messages
            model: OpenAI model name
            tools: Available tools for function calling
            tool_choice: Tool choice strategy
            response_format: Response format specification

        Returns:
            Raw OpenAI chat completion response
        """
        kwargs = {"model": model or self.model, "messages": messages}

        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice

        if response_format:
            kwargs["response_format"] = response_format

        response = await self.client.chat.completions.create(**kwargs)
        return response

    async def prompt_with_auto_tools(
        self,
        message_system,  # MessageSystem object
        tools: List[Dict[str, Any]] = None,
        model: str = None,
    ) -> Dict[str, Any]:
        """
        Single prompt cycle with automatic tool calling.
        If LLM returns tool calls, auto-execute them and return final result.

        Args:
            message_system: MessageSystem object to manage conversation
            tools: Available tools for function calling
            model: OpenAI model name

        Returns:
            Dict with assistant_message, tool_results, and has_tool_calls
        """
        if tools and not self._tool_executor:
            raise ValueError("Tool executor not set. Call set_tool_executor() first.")

        # Get messages in OpenAI format from MessageSystem
        messages = message_system.to_openai_format()

        # Get LLM response
        response = await self.chat_completion(
            messages=messages, model=model, tools=tools, tool_choice="auto"
        )

        assistant_message = response.choices[0].message
        
        # Debug: Check if we got a response
        if not assistant_message.content and not assistant_message.tool_calls:
            print("⚠️  WARNING: LLM returned empty response with no tool calls!")
            print(f"Response object: {response}")

        # Add assistant response to MessageSystem
        message_system.add_assistant_message(
            content=assistant_message.content,
            tool_calls=assistant_message.tool_calls if assistant_message.tool_calls else None
        )

        tool_results = []

        # Handle tool calls if any
        if assistant_message.tool_calls:
            print(f"🤖 LLM: {assistant_message.content or '(calling tools)'}")

            for tool_call in assistant_message.tool_calls:
                result_info = await self._execute_tool_with_retries(message_system, tool_call, max_retries=3)
                tool_results.append(result_info)

            # After executing all tools, make another LLM call to process results
            print("🔄 Making follow-up LLM call to process tool results...")
            
            follow_up_response = await self.chat_completion(
                messages=message_system.to_openai_format(), 
                model=model,
                tool_choice="none"
            )
            
            final_message = follow_up_response.choices[0].message
            print(f"🤖 LLM Final: {final_message.content}")
            
            # Add final response to messages
            message_system.add_assistant_message(
                content=final_message.content
            )
            
        else:
            print(f"🤖 LLM: {assistant_message.content}")

        return {
            "assistant_message": assistant_message,
            "tool_results": tool_results,
            "has_tool_calls": bool(assistant_message.tool_calls),
        }

    async def list_available_models(self) -> List[Dict[str, Any]]:
        """
        List available models from OpenAI API.
        
        Returns:
            List of available models with their details
        """
        try:
            models_response = await self.client.models.list()
            models = []
            
            for model in models_response.data:
                models.append({
                    "id": model.id,
                    "object": model.object,
                    "created": model.created,
                    "owned_by": model.owned_by,
                })
            
            # Sort by model ID for better display
            models.sort(key=lambda x: x["id"])
            return models
            
        except Exception as e:
            print(f"❌ Failed to fetch models: {e}")
            return []
