"""Conversation coordinator — orchestrates agent turns."""

from __future__ import annotations

import traceback

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from crosstalk.agents import create_agent, AgentBackend
from crosstalk.logger import append_message
from crosstalk.models import Conversation, Message
from crosstalk.personas import load_persona

console = Console()


async def run_conversation(conv: Conversation) -> None:
    """Run the main conversation loop."""
    conv.save_meta()

    agents: dict[str, AgentBackend] = {}
    for name in conv.agents:
        agents[name] = create_agent(name)

    # Pre-load all persona skills
    persona_prompts: dict[str, str] = {}
    for agent_name in conv.agents:
        persona_name = conv.personas.get(agent_name, "default")
        persona_prompts[agent_name] = load_persona(persona_name)

    console.print(
        Panel(
            f"[bold]{conv.topic}[/bold]\n"
            f"Agents: {', '.join(conv.agents)} | Max turns: {conv.max_turns}",
            title="Crosstalk",
            border_style="blue",
        )
    )

    turn = len(conv.messages)

    while turn < conv.max_turns:
        agent_name = conv.agents[turn % len(conv.agents)]
        agent = agents[agent_name]
        persona_name = conv.personas.get(agent_name, "default")
        persona_prompt = persona_prompts[agent_name]

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

        console.print(
            Panel(
                Markdown(response),
                title=f"{agent_name.capitalize()} ({persona_name})",
                border_style="green" if agent_name == "claude" else "cyan",
            )
        )

        turn += 1

        if "CONSENSUS" in response.upper():
            console.print("\n[bold green]Consensus reached![/bold green]")
            break

    console.print(
        f"\n[bold]Conversation complete.[/bold] "
        f"{len(conv.messages)} turns logged to {conv.conv_dir}"
    )
