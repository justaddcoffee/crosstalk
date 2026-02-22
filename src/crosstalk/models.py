"""Message and Conversation data models."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class Message:
    sender: str
    content: str
    role: str = "message"
    persona: str = "default"
    id: str = field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:8]}")
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: dict = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, line: str) -> Message:
        data = json.loads(line)
        return cls(**data)


@dataclass
class Conversation:
    topic: str
    agents: list[str]
    personas: dict[str, str]  # agent_name -> persona_name
    max_turns: int
    conv_id: str = field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    started: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    messages: list[Message] = field(default_factory=list)

    @property
    def conv_dir(self) -> Path:
        return Path("conversations") / self.conv_id

    @property
    def messages_path(self) -> Path:
        return self.conv_dir / "messages.jsonl"

    @property
    def transcript_path(self) -> Path:
        return self.conv_dir / "transcript.md"

    @property
    def meta_path(self) -> Path:
        return self.conv_dir / "meta.json"

    def save_meta(self) -> None:
        self.conv_dir.mkdir(parents=True, exist_ok=True)
        meta = {
            "conv_id": self.conv_id,
            "topic": self.topic,
            "agents": self.agents,
            "personas": self.personas,
            "max_turns": self.max_turns,
            "started": self.started,
        }
        self.meta_path.write_text(json.dumps(meta, indent=2))

    @classmethod
    def load(cls, conv_id: str) -> Conversation:
        conv_dir = Path("conversations") / conv_id
        meta = json.loads((conv_dir / "meta.json").read_text())
        conv = cls(
            topic=meta["topic"],
            agents=meta["agents"],
            personas=meta["personas"],
            max_turns=meta["max_turns"],
            conv_id=meta["conv_id"],
            started=meta["started"],
        )
        messages_path = conv_dir / "messages.jsonl"
        if messages_path.exists():
            for line in messages_path.read_text().strip().splitlines():
                if line:
                    conv.messages.append(Message.from_json(line))
        return conv
