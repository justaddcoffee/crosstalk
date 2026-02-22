"""CLI entrypoint for Crosstalk."""

from __future__ import annotations

import asyncio
from pathlib import Path

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

from crosstalk.coordinator import run_conversation
from crosstalk.models import Conversation
from crosstalk.personas import available_personas, load_persona

console = Console()
CONVERSATIONS_DIR = Path("conversations")


@click.group()
def cli() -> None:
    """Crosstalk — Multi-agent chat and collaboration."""


@cli.command()
@click.argument("topic")
@click.option(
    "--agents", "-a", default="claude,codex",
    help="Comma-separated agent names (default: claude,codex)",
)
@click.option(
    "--max-turns", "-t", default=20, type=int,
    help="Maximum conversation turns (default: 20)",
)
@click.option(
    "--personas", "-p", default=None,
    help="Comma-separated personas matching agents (e.g., architect,critic)",
)
def start(topic: str, agents: str, max_turns: int, personas: str | None) -> None:
    """Start a new multi-agent conversation."""
    agent_list = [a.strip() for a in agents.split(",")]

    if personas:
        persona_list = [p.strip() for p in personas.split(",")]
        if len(persona_list) != len(agent_list):
            raise click.BadParameter(
                f"Number of personas ({len(persona_list)}) must match "
                f"number of agents ({len(agent_list)})"
            )
        persona_map = dict(zip(agent_list, persona_list))
    else:
        persona_map = {a: "default" for a in agent_list}

    # Validate persona names by attempting to load them
    avail = available_personas()
    for name, persona in persona_map.items():
        if persona not in avail:
            raise click.BadParameter(
                f"Unknown persona '{persona}' for agent '{name}'. "
                f"Available: {avail}"
            )

    conv = Conversation(
        topic=topic,
        agents=agent_list,
        personas=persona_map,
        max_turns=max_turns,
    )

    asyncio.run(run_conversation(conv))


@cli.command("list")
def list_conversations() -> None:
    """List past conversations."""
    if not CONVERSATIONS_DIR.exists():
        console.print("[dim]No conversations yet.[/dim]")
        return

    table = Table(title="Conversations")
    table.add_column("ID", style="cyan")
    table.add_column("Topic", style="white")
    table.add_column("Agents", style="green")
    table.add_column("Turns", style="yellow", justify="right")
    table.add_column("Started", style="dim")

    for conv_dir in sorted(CONVERSATIONS_DIR.iterdir()):
        meta_path = conv_dir / "meta.json"
        if not meta_path.exists():
            continue
        conv = Conversation.load(conv_dir.name)
        table.add_row(
            conv.conv_id,
            conv.topic[:50],
            ", ".join(conv.agents),
            str(len(conv.messages)),
            conv.started[:19],
        )

    console.print(table)


@cli.command()
@click.argument("conv_id")
def view(conv_id: str) -> None:
    """View a conversation transcript."""
    conv_dir = CONVERSATIONS_DIR / conv_id
    if not conv_dir.exists():
        console.print(f"[red]Conversation '{conv_id}' not found.[/red]")
        raise SystemExit(1)

    transcript_path = conv_dir / "transcript.md"
    if transcript_path.exists():
        console.print(Markdown(transcript_path.read_text()))
    else:
        console.print("[dim]No transcript available.[/dim]")


@cli.command()
@click.argument("conv_id")
@click.option(
    "--extra-turns", "-t", default=10, type=int,
    help="Additional turns to run (default: 10)",
)
def resume(conv_id: str, extra_turns: int) -> None:
    """Resume a past conversation with additional turns."""
    conv_dir = CONVERSATIONS_DIR / conv_id
    if not conv_dir.exists():
        console.print(f"[red]Conversation '{conv_id}' not found.[/red]")
        raise SystemExit(1)

    conv = Conversation.load(conv_id)
    conv.max_turns = len(conv.messages) + extra_turns

    console.print(
        f"[bold]Resuming conversation '{conv_id}'[/bold] — "
        f"{len(conv.messages)} existing turns, adding up to {extra_turns} more"
    )

    asyncio.run(run_conversation(conv))


@cli.command("personas")
def list_personas() -> None:
    """List available persona skills."""
    table = Table(title="Available Personas")
    table.add_column("Name", style="cyan")
    table.add_column("Preview", style="dim")

    for name in available_personas():
        content = load_persona(name)
        # Show first non-header line as preview
        preview = ""
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                preview = line[:80]
                break
        table.add_row(name, preview)

    console.print(table)
