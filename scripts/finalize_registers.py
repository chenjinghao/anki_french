#!/usr/bin/env python3
"""Rebuild Register fields deterministically from the original German values."""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPLACEMENTS = {
    "Fiktion": "fiction",
    "Sachtext": "nonfiction",
    "Mündlich": "spoken",
    "# Beispiel: ↘Sachtext ↗Mündlich": "# Example: ↘nonfiction ↗spoken",
}


def git_show(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    proc = subprocess.run(
        ["git", "show", f"origin/main:{rel}"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    return proc.stdout


def register_line(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("Register:"):
            return line
    return None


def english_register(line: str) -> str:
    for old, new in REPLACEMENTS.items():
        line = line.replace(old, new)
    return line


def main() -> None:
    for path in sorted((ROOT / "cards").glob("*.yml")):
        original = register_line(git_show(path))
        if original is None:
            continue
        replacement = english_register(original)
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        for i, raw in enumerate(lines):
            if raw.startswith("Register:"):
                newline = "\n" if raw.endswith("\n") else ""
                lines[i] = replacement + newline
                break
        path.write_text("".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
