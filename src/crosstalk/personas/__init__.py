"""Persona skill system for Crosstalk agents."""

from __future__ import annotations

from pathlib import Path

PERSONAS_DIR = Path(__file__).parent

_PERSONA_CACHE: dict[str, str] = {}


def available_personas() -> list[str]:
    """Return names of all available persona skill files."""
    return sorted(
        p.stem for p in PERSONAS_DIR.glob("*.md")
    )


def load_persona(name: str) -> str:
    """Load a persona skill prompt by name."""
    if name in _PERSONA_CACHE:
        return _PERSONA_CACHE[name]

    path = PERSONAS_DIR / f"{name}.md"
    if not path.exists():
        raise ValueError(
            f"Unknown persona '{name}'. Available: {available_personas()}"
        )

    content = path.read_text().strip()
    _PERSONA_CACHE[name] = content
    return content
