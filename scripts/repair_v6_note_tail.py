#!/usr/bin/env python3
"""Repair v6 note fields without stopping at whitespace-only lines."""
from __future__ import annotations

import argparse
from pathlib import Path

from repair_v6 import AIMER_NOTE


def replace_note_field(text: str, replacement: str) -> str:
    lines = text.splitlines(keepends=True)
    start = next((i for i, line in enumerate(lines) if line.startswith("Notiz:")), None)
    if start is None:
        return text
    end = start + 1
    while end < len(lines):
        line = lines[end]
        if line.strip() and not line.startswith((" ", "\t")):
            break
        end += 1
    replacement_lines = replacement.splitlines(keepends=True)
    if replacement_lines and not replacement_lines[-1].endswith("\n"):
        replacement_lines[-1] += "\n"
    return "".join(lines[:start] + replacement_lines + lines[end:])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--paths-file", required=True)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    paths = [
        line.strip()
        for line in Path(args.paths_file).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    for rel in paths:
        if rel != "cards/0242_aimer.yml":
            continue
        path = root / rel
        text = path.read_text(encoding="utf-8")
        path.write_text(replace_note_field(text, AIMER_NOTE), encoding="utf-8")


if __name__ == "__main__":
    main()
