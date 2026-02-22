"""Conversation coordinator — orchestrates agent turns."""

from __future__ import annotations

import traceback
from datetime import datetime, timezone

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from crosstalk.agents import create_agent, AgentBackend
from crosstalk.logger import append_message
from crosstalk.models import Conversation, Message
from crosstalk.personas import load_persona


async def run_conversation(conv: Conversation, quiet: bool = False) -> None:
    """Run the main conversation loop."""
    console = Console(stderr=True)

    conv.save_meta()

    agents: dict[str, AgentBackend] = {}
    for name in conv.agents:
        agents[name] = create_agent(name)

    # Pre-load all persona skills
    persona_prompts: dict[str, str] = {}
    for agent_name in conv.agents:
        persona_name = conv.personas.get(agent_name, "default")
        persona_prompts[agent_name] = load_persona(persona_name)

    if not quiet:
        agents_str = ", ".join(
            f"{a} ({conv.personas.get(a, 'default')})" for a in conv.agents
        )
        console.print(
            Panel(
                f"[bold]{conv.topic}[/bold]\n"
                f"Agents: {agents_str}\n"
                f"Max turns: {conv.max_turns} | ID: {conv.conv_id}",
                title="Crosstalk",
                border_style="blue",
            )
        )

    turn = len(conv.messages)
    consensus = False

    while turn < conv.max_turns:
        agent_name = conv.agents[turn % len(conv.agents)]
        agent = agents[agent_name]
        persona_name = conv.personas.get(agent_name, "default")
        persona_prompt = persona_prompts[agent_name]

        if not quiet:
            console.print(
                f"\n[dim]Turn {turn + 1}/{conv.max_turns} — "
                f"waiting for {agent_name} ({persona_name})...[/dim]"
            )

        try:
            response = await agent.send(conv.messages, persona_prompt, conv.topic)
        except Exception as e:
            console.print(
                Panel(
                    f"[red bold]Error from {agent_name}[/red bold]\n\n"
                    f"{e}\n\n"
                    f"[dim]{traceback.format_exc()}[/dim]",
                    title="Agent Error",
                    border_style="red",
                )
            )
            break

        if not response:
            console.print(f"[yellow]Warning: empty response from {agent_name}[/yellow]")
            break

        msg = Message(
            sender=agent_name,
            content=response,
            persona=persona_name,
            metadata={"turn": turn + 1},
        )
        append_message(conv, msg)

        if not quiet:
            console.print(
                Panel(
                    Markdown(response),
                    title=f"{agent_name.capitalize()} ({persona_name})",
                    border_style="green" if agent_name == "claude" else "cyan",
                )
            )

        turn += 1

        if "CONSENSUS" in response.upper():
            consensus = True
            if not quiet:
                console.print("\n[bold green]Consensus reached![/bold green]")
            break

    # Always print the summary
    _print_summary(console, conv, consensus)


def _print_summary(console: Console, conv: Conversation, consensus: bool) -> None:
    """Print an end-of-run summary."""
    table = Table(
        title="Conversation Summary",
        show_header=False,
        border_style="blue",
        padding=(0, 1),
    )
    table.add_column("Key", style="bold")
    table.add_column("Value")

    table.add_row("Topic", conv.topic)
    table.add_row("ID", conv.conv_id)
    table.add_row("Turns", str(len(conv.messages)))

    speakers = {}
    for msg in conv.messages:
        label = f"{msg.sender} ({msg.persona})"
        speakers[label] = speakers.get(label, 0) + 1
    speakers_str = ", ".join(f"{k}: {v}" for k, v in speakers.items())
    table.add_row("Speakers", speakers_str)

    outcome = "Consensus" if consensus else f"Completed ({len(conv.messages)} turns)"
    table.add_row("Outcome", outcome)
    table.add_row("Transcript", str(conv.transcript_path))
    table.add_row("Log", str(conv.messages_path))

    console.print()
    console.print(table)
