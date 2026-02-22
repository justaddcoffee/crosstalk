# Crosstalk

Multi-agent chat and collaboration system. Two or more AI agents (Claude, Codex) debate ideas, review designs, and collaborate — all orchestrated from your terminal.

Agents communicate via structured message passing. Every conversation is logged as JSONL and rendered as a Markdown transcript.

## Prerequisites

- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) (`claude`) — authenticated via Claude Max
- [Codex CLI](https://github.com/openai/codex) (`codex`) — authenticated via subscription
- [uv](https://docs.astral.sh/uv/)

## Quick Start

```bash
git clone https://github.com/justaddcoffee/crosstalk.git
cd crosstalk
uv sync
```

Run a debate:

```bash
uv run crosstalk start "Debate: tabs vs spaces" --agents claude,codex --max-turns 4 --personas architect,critic
```

## Usage

### Start a conversation

```bash
uv run crosstalk start "<topic>" --agents claude,codex --max-turns <n> --personas <persona1>,<persona2>
```

### List past conversations

```bash
uv run crosstalk list
```

### View a transcript

```bash
uv run crosstalk view <conv_id>
```

### Resume a conversation

```bash
uv run crosstalk resume <conv_id> --extra-turns 10
```

## Personas

Each agent is assigned a persona that shapes how it contributes. Personas are Markdown files in `src/crosstalk/personas/`.

| Persona | Role |
|---|---|
| `architect` | System design, trade-offs, clean abstractions |
| `critic` | Challenge assumptions, find edge cases |
| `implementer` | Concrete code, practical solutions |
| `default` | Balanced collaborative peer |

List available personas:

```bash
uv run crosstalk personas
```

Add a custom persona by dropping a new `.md` file in `src/crosstalk/personas/`.

## How It Works

1. You provide a topic, agents, and personas
2. The coordinator loops through agents in round-robin order
3. Each agent receives the full conversation history plus its persona as a system prompt
4. Responses are logged to `conversations/<id>/messages.jsonl` and rendered to `transcript.md`
5. The loop stops at max turns or when an agent says "CONSENSUS"

Agents are invoked via their CLI tools (`claude -p`, `codex exec`) as subprocesses — no API keys needed.
