"""Codex CLI agent adapter."""

from __future__ import annotations

import os
import subprocess
import tempfile

from crosstalk.agents.base import AgentBackend
from crosstalk.models import Message

# Env vars to strip so child CLIs don't think they're nested
_STRIP_VARS = {"CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT"}


class CodexAgent(AgentBackend):
    MODEL = "gpt-5.3-codex"

    async def send(self, history: list[Message], persona_prompt: str, topic: str) -> str:
        prompt = self.build_conversation_prompt(history, topic)

        if persona_prompt:
            prompt = f"{persona_prompt}\n\n{prompt}"

        # Write response to a temp file so we can capture it cleanly
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as out_file:
            out_path = out_file.name

        cmd = [
            "codex", "exec",
            prompt,
            "--model", self.MODEL,
            "--full-auto",
            "-o", out_path,
        ]

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
                f"Codex CLI failed (exit {result.returncode})\n"
                f"  stderr: {stderr}\n"
                f"  stdout: {stdout}"
            )

        # Read from output file first, fall back to stdout
        try:
            from pathlib import Path
            content = Path(out_path).read_text().strip()
            if content:
                return content
        except Exception:
            pass

        return result.stdout.strip()
