#!/usr/bin/env python3
"""Normalize nonstandard quoted Beispielsätze scalars to block scalars per shard."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import yaml


def select_shard(paths: Iterable[Path], shard: int, shards: int) -> list[Path]:
    ordered = sorted(paths, key=lambda p: p.as_posix())
    return [p for i, p in enumerate(ordered) if i % shards == shard]


def normalize_card(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    start = next((i for i, line in enumerate(lines) if line.startswith("Beispielsätze:")), None)
    if start is None or not lines[start].lstrip().startswith('Beispielsätze: "'):
        return

    data = yaml.safe_load(text)
    examples = data.get("Beispielsätze")
    if not isinstance(examples, str):
        raise ValueError(f"Could not decode Beispielsätze in {path}")

    end = start + 1
    while end < len(lines):
        line = lines[end]
        if line.strip() == "":
            break
        if line.startswith((" ", "\t")):
            end += 1
            continue
        break

    replacement = ["Beispielsätze: |-\n"]
    example_lines = examples.split("\n")
    for value in example_lines:
        replacement.append(("  " + value if value else "") + "\n")

    lines[start:end] = replacement
    path.write_text("".join(lines), encoding="utf-8")
    print(f"Normalized quoted examples: {path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--shard", type=int, required=True)
    parser.add_argument("--shards", type=int, required=True)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    for path in select_shard((root / "cards").glob("*.yml"), args.shard, args.shards):
        normalize_card(path)


if __name__ == "__main__":
    main()
