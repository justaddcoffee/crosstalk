"""Agent backends for Crosstalk."""

from crosstalk.agents.base import AgentBackend
from crosstalk.agents.claude import ClaudeAgent
from crosstalk.agents.codex import CodexAgent

AGENT_REGISTRY: dict[str, type[AgentBackend]] = {
    "claude": ClaudeAgent,
    "codex": CodexAgent,
}


def create_agent(name: str) -> AgentBackend:
    if name not in AGENT_REGISTRY:
        raise ValueError(
            f"Unknown agent '{name}'. Available: {list(AGENT_REGISTRY.keys())}"
        )
    return AGENT_REGISTRY[name](name=name)
