#!/usr/bin/env python3
"""Finalize English-facing repository docs from translated card sources."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def card_definition(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("Definition:"):
            return line.split(":", 1)[1].strip()
    return ""


def sync_words() -> None:
    path = ROOT / "WORDS.md"
    lines = path.read_text(encoding="utf-8").splitlines()
    card_by_rank = {}
    for card in sorted((ROOT / "cards").glob("*.yml")):
        rank = int(card.name.split("_", 1)[0])
        card_by_rank[rank] = card_definition(card)

    out = []
    for i, line in enumerate(lines):
        if i == 0:
            out.append("| Rank | Word | Definition | Example Sentences | Note | Link |")
            continue
        m = re.match(r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*(.*?)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*\[.*?\]\((.*?)\)\s*\|$", line)
        if not m:
            out.append(line)
            continue
        rank = int(m.group(1))
        word = m.group(2).strip()
        examples = m.group(4).strip()
        note = m.group(5).strip()
        link = m.group(6).strip()
        definition = card_by_rank.get(rank, m.group(3).strip())
        out.append(f"| {rank} | {word} | {definition} | {examples} | {note} | [Edit]({link}) |")
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def write_readme() -> None:
    text = """# French 5000

Help improve **French 5000**, an Anki deck for English speakers learning French. The deck contains the 5,000 most frequent French words, with extensive example sentences, grammar notes, audio, and more.

This repository is the English-learning version of the original German-to-French deck. French source text is preserved; German learner-facing definitions, translations, grammar explanations, and interface text are translated into English.

## Contributing

The [cards](cards) directory contains all 5,000 cards in YAML format.

1. Fork this repository.
2. Edit card files in `cards`.
3. Commit your changes.
4. Open a pull request.

## Grammar

The [grammar](grammar) directory contains the grammar-library entries. The directory hierarchy is also used to organize the grammar library.

A grammar entry can be embedded in a card note with `<grammar data-id="ID"></grammar>`. Some internal IDs and schema field names remain in German for compatibility with the original Anki note type; learner-facing text is English.

## License

The deck itself is released under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). Source code in [card_templates](card_templates) is licensed under Apache 2.0.

## Overview

The repository contains **5,000 cards** with **149,711 example sentences** (29.9 per card on average). **2,568 cards** include an additional note.

See the [complete word list](WORDS.md).
"""
    (ROOT / "README.md").write_text(text, encoding="utf-8")


if __name__ == "__main__":
    sync_words()
    write_readme()
