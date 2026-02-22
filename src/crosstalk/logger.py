"""JSONL logging and Markdown transcript rendering."""

from __future__ import annotations

from datetime import datetime

from crosstalk.models import Conversation, Message


def append_message(conv: Conversation, message: Message) -> None:
    """Append a message to the JSONL log and re-render the transcript."""
    conv.messages.append(message)
    conv.conv_dir.mkdir(parents=True, exist_ok=True)

    with open(conv.messages_path, "a") as f:
        f.write(message.to_json() + "\n")

    render_transcript(conv)


def render_transcript(conv: Conversation) -> None:
    """Render the full Markdown transcript from conversation state."""
    started_dt = datetime.fromisoformat(conv.started)
    started_str = started_dt.strftime("%Y-%m-%d %H:%M")

    agents_str = ", ".join(
        f"{a} ({conv.personas.get(a, 'default')})" for a in conv.agents
    )

    lines = [
        f"# Conversation: {conv.topic}",
        f"Started: {started_str} | Agents: {agents_str} | Max turns: {conv.max_turns}",
        "",
    ]

    for i, msg in enumerate(conv.messages):
        ts = datetime.fromisoformat(msg.timestamp)
        ts_str = ts.strftime("%H:%M:%S")
        persona_label = f" ({msg.persona})" if msg.persona != "default" else ""
        turn_num = i + 1

        lines.append("---")
        lines.append(
            f"## Turn {turn_num} — {msg.sender.capitalize()}{persona_label} [{ts_str}]"
        )
        lines.append("")
        lines.append(msg.content)
        lines.append("")

    conv.transcript_path.write_text("\n".join(lines))
