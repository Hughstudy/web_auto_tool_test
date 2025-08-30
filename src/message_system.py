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

    def clear(self):
        """Clear all messages."""
        self.messages.clear()

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
