"""Abstract agent backend interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from crosstalk.models import Message


class AgentBackend(ABC):
    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    async def send(self, history: list[Message], persona_prompt: str, topic: str) -> str:
        """Send conversation history to the agent and return its response text."""

    def build_conversation_prompt(
        self, history: list[Message], topic: str
    ) -> str:
        lines = [f"Topic: {topic}", "", "Conversation so far:", ""]
        for msg in history:
            persona_label = f" ({msg.persona})" if msg.persona != "default" else ""
            lines.append(f"[{msg.sender}{persona_label}]: {msg.content}")
            lines.append("")
        lines.append(
            "It's your turn. Respond thoughtfully, building on the conversation. "
            "If you believe the group has reached consensus, include the word CONSENSUS."
        )
        return "\n".join(lines)
