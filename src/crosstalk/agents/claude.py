"""Claude Code CLI agent adapter."""

from __future__ import annotations

import json
import os
import subprocess

from crosstalk.agents.base import AgentBackend
from crosstalk.models import Message

# Env vars to strip so child CLIs don't think they're nested
_STRIP_VARS = {"CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT"}


class ClaudeAgent(AgentBackend):
    MODEL = "claude-sonnet-4-20250514"

    async def send(self, history: list[Message], persona_prompt: str, topic: str) -> str:
        prompt = self.build_conversation_prompt(history, topic)

        cmd = [
            "claude",
            "-p", prompt,
            "--output-format", "json",
            "--model", self.MODEL,
        ]
        if persona_prompt:
            cmd.extend(["--system-prompt", persona_prompt])

        env = {k: v for k, v in os.environ.items() if k not in _STRIP_VARS}

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            env=env,
        )

        if result.returncode != 0:
            stderr = result.stderr.strip()
            stdout = result.stdout.strip()
            raise RuntimeError(
                f"Claude CLI failed (exit {result.returncode})\n"
                f"  stderr: {stderr}\n"
                f"  stdout: {stdout}"
            )

        # --output-format json returns a JSON object with a "result" field
        try:
            data = json.loads(result.stdout)
            return data.get("result", result.stdout).strip()
        except json.JSONDecodeError:
            return result.stdout.strip()
