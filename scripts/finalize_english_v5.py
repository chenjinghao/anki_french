#!/usr/bin/env python3
"""Run the existing English finalizer with isolated semantic example parsing for v5."""
from __future__ import annotations

import re

import yaml

import finalize_english as base


EXTRA_GERMAN_SOURCE_WORDS = {
    "man", "verwendet", "benutzt", "braucht", "wurde", "geboren", "jahr", "ort",
    "geschehens", "vollen", "sinne", "wortes", "verschiedene", "bedeutungen",
    "allgemeinen", "drückt", "grobe", "unhöfliche", "handlung", "alle",
    "grundbedeutung", "abgeleitet", "entwickelte", "kontexte", "irgendwann", "laufe",
    "zeitspanne", "mitglied", "teams", "adverbien", "ortes", "wechsel", "hilfsverbs",
    "hauptverbs", "indikativ", "bedeutet", "feststellen", "begreifen", "anstelle",
    "umschreibung", "hab", "angst", "monat", "weder", "noch", "angekommen", "gibt",
    "musste", "gehen", "verstehst", "schon", "wieder", "keine", "substantivs",
}

base.GERMAN_SOURCE_WORDS.update(EXTRA_GERMAN_SOURCE_WORDS)
base.GERMAN_SOURCE_EXACT.update({
    "Jahr", "keine", "schon wieder", "weder ... noch", "Wechsel des Hilfsverbs",
    "Adverbien des Ortes:", "Ort des Geschehens",
})


def _example_field_yaml(text: str) -> str:
    """Extract only the top-level Beispielsätze YAML field and its continuation lines."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith("Beispielsätze:"):
            start = i
            break
    if start is None:
        return ""

    field_lines = [lines[start]]
    for line in lines[start + 1 :]:
        # A non-empty, non-indented line starts the next top-level YAML field/comment.
        if line and not line.startswith((" ", "\t")):
            break
        field_lines.append(line)
    return "\n".join(field_lines) + "\n"


def semantic_example_blocks(text: str) -> list[list[str]]:
    snippet = _example_field_yaml(text)
    if not snippet:
        return []
    try:
        data = yaml.safe_load(snippet)
    except yaml.YAMLError as exc:
        raise ValueError(f"Could not parse Beispielsätze field: {exc}") from exc

    value = data.get("Beispielsätze", "") if isinstance(data, dict) else ""
    if not isinstance(value, str):
        return []

    blocks: list[list[str]] = []
    for block in re.split(r"\n\s*\n", value.strip()):
        if not block.strip():
            continue
        blocks.append(block.splitlines())
    return blocks


base.example_blocks = semantic_example_blocks


if __name__ == "__main__":
    base.finalize_templates()
    base.validate_translation()
    base.sync_words()
    base.write_readme()
