"""
Message System for managing OpenAI chat messages with proper formatting.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class Message:
    """Individual message in the conversation."""

    role: str  # "user", "assistant", "system", "tool"
    content: Optional[str] = None
    tool_calls: Optional[List[Any]] = None
    tool_call_id: Optional[str] = None

    def to_openai_format(self) -> Dict[str, Any]:
        """Convert to OpenAI API format."""
        msg = {"role": self.role}

        if self.content is not None:
            msg["content"] = self.content

        if self.tool_calls:
            msg["tool_calls"] = self.tool_calls

        if self.tool_call_id:
            msg["tool_call_id"] = self.tool_call_id

        return msg


class MessageSystem:
    """Centralized message management system for conversation tracking."""

    def __init__(self):
        self.messages: List[Message] = []
        self._conversation_id = None
        self.last_request: Optional[str] = None

    def clear(self):
        """Clear all messages."""
        self.messages.clear()

    def set_last_request(self, request: str) -> "MessageSystem":
        """Set the last user request for context preservation."""
        self.last_request = request
        return self

    def add_user_message(self, content: str) -> "MessageSystem":
        """Add a user message."""
        self.messages.append(Message(role="user", content=content))
        return self

    def add_system_message(self, content: str) -> "MessageSystem":
        """Add a system message."""
        self.messages.append(Message(role="system", content=content))
        return self

    def add_assistant_message(
        self, content: Optional[str] = None, tool_calls: Optional[List[Any]] = None
    ) -> "MessageSystem":
        """Add an assistant message with optional tool calls."""
        self.messages.append(
            Message(role="assistant", content=content, tool_calls=tool_calls)
        )
        return self

    def add_tool_result(self, tool_call_id: str, result: str) -> "MessageSystem":
        """Add a tool execution result."""
        self.messages.append(
            Message(role="tool", content=result, tool_call_id=tool_call_id)
        )
        return self

    def append_message(self, message: Message) -> "MessageSystem":
        """Append a Message object directly."""
        self.messages.append(message)
        return self

    def append_raw(self, message_dict: Dict[str, Any]) -> "MessageSystem":
        """Append a raw message dictionary (for compatibility)."""
        msg = Message(
            role=message_dict["role"],
            content=message_dict.get("content"),
            tool_calls=message_dict.get("tool_calls"),
            tool_call_id=message_dict.get("tool_call_id"),
        )
        self.messages.append(msg)
        return self

    def to_openai_format(self) -> List[Dict[str, Any]]:
        """Convert all messages to OpenAI API format."""
        return [msg.to_openai_format() for msg in self.messages]

    def get_last_message(self) -> Optional[Message]:
        """Get the last message in the conversation."""
        return self.messages[-1] if self.messages else None

    def get_last_n_messages(self, n: int) -> List[Message]:
        """Get the last N messages."""
        return self.messages[-n:] if len(self.messages) >= n else self.messages

    def count(self) -> int:
        """Get total number of messages."""
        return len(self.messages)

    def get_messages_by_role(self, role: str) -> List[Message]:
        """Get all messages by a specific role."""
        return [msg for msg in self.messages if msg.role == role]

    def get_conversation_summary(self) -> str:
        """Get a text summary of the conversation."""
        summary = []
        for msg in self.messages:
            if msg.role == "user":
                summary.append(f"USER: {msg.content}")
            elif msg.role == "assistant":
                if msg.tool_calls:
                    tool_names = (
                        [tc.function.name for tc in msg.tool_calls]
                        if hasattr(msg.tool_calls[0], "function")
                        else ["unknown"]
                    )
                    summary.append(f"ASSISTANT: Used tools: {', '.join(tool_names)}")
                    if msg.content:
                        summary.append(f"ASSISTANT: {msg.content}")
                else:
                    summary.append(f"ASSISTANT: {msg.content}")
            elif msg.role == "tool":
                summary.append(
                    f"TOOL_RESULT: {msg.content}"
                )
            elif msg.role == "system":
                summary.append(f"SYSTEM: {msg.content}")

        return "\n".join(summary)
    
    def estimate_token_count(self) -> int:
        """Estimate token count of the conversation (rough approximation)."""
        text = self.get_conversation_summary()
        # Rough approximation: ~4 characters per token
        return len(text) // 4
    
    async def compact_conversation(self, llm_client, target_words: int = 5000) -> "MessageSystem":
        """
        Compact the conversation to reduce token usage while preserving key information.
        
        Args:
            llm_client: LLM client to use for summarization
            target_words: Target word count for the compacted conversation
            
        Returns:
            New MessageSystem with compacted messages
        """
        if len(self.messages) <= 2:  # Don't compact very short conversations
            return self.clone()
            
        # Use last_request if available, otherwise get first user message
        request_to_use = self.last_request
        if not request_to_use:
            for msg in self.messages:
                if msg.role == "user":
                    request_to_use = msg.content
                    break
                    
        if not request_to_use:
            return self.clone()
            
        # Build summary of accomplishments and results
        conversation_text = self.get_conversation_summary()
        
        # Create summarization prompt
        compact_prompt = f"""Please create a concise summary of this task execution conversation.

FULL CONVERSATION:
{conversation_text}

Create a summary that includes:
1. What has been accomplished so far
2. Key results and findings
3. Current status of the task
4. Any important context needed to continue

Keep the summary focused and under {target_words} words while preserving all essential information for task continuation.

Format the response as a clear, structured summary without any markdown or special formatting."""

        try:
            # Use LLM to create compact summary
            messages = [{"role": "user", "content": compact_prompt}]
            response = await llm_client.chat_completion(messages=messages, tool_choice="none")
            summary_content = response.choices[0].message.content
            
            # Create new MessageSystem with compacted conversation
            compacted = MessageSystem()
            
            # Add the compacted summary as a single user message
            compact_user_message = f"""Task: {request_to_use}

Progress Summary:
{summary_content}

Please continue with the task based on this progress summary."""
            
            compacted.add_user_message(compact_user_message)
            
            return compacted
            
        except Exception as e:
            print(f"⚠️  Failed to compact conversation: {e}")
            # Fallback: return clone of original
            return self.clone()

    def clone(self) -> "MessageSystem":
        """Create a deep copy of the message system."""
        new_system = MessageSystem()
        for msg in self.messages:
            new_system.messages.append(
                Message(
                    role=msg.role,
                    content=msg.content,
                    tool_calls=msg.tool_calls.copy() if msg.tool_calls else None,
                    tool_call_id=msg.tool_call_id,
                )
            )
        return new_system

    def __len__(self) -> int:
        """Support len() function."""
        return len(self.messages)

    def __str__(self) -> str:
        """String representation for debugging."""
        return f"MessageSystem({len(self.messages)} messages)"

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return f"MessageSystem(messages={len(self.messages)}, last_role={self.get_last_message().role if self.messages else None})"
