#!/usr/bin/env python3
"""Run the existing English finalizer with isolated semantic example parsing for v5."""
from __future__ import annotations

import html
import re
from pathlib import Path

import yaml

import finalize_english as base


ROOT = Path(__file__).resolve().parents[1]

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

KNOWN_NON_GERMAN = {
    "Harry Potter à l'école des sorciers (1997)",
}
_original_source_likely_german = base.source_likely_german


def source_likely_german_v5(text: str) -> bool:
    value = html.unescape(text).strip()
    if value in KNOWN_NON_GERMAN:
        return False
    return _original_source_likely_german(text)


base.source_likely_german = source_likely_german_v5


def repair_final_residuals() -> None:
    """Apply the final path-specific v5 substitutions before strict QA."""
    replacements = {
        "cards/1890_foutre.yml": [
            ("viel bedeuten", "mean"),
            ('wie "machen", "tun",', 'things like "do", "make",'),
            ('"geben", "stecken" oder "ficken".', '"give", "put", or "fuck".'),
            ("so viel wie", "means"),
            ('"vögeln"', '"fuck"'),
        ],
        "grammar/07 Pronomen/13 Die Indefinitbegleiter.html": [
            ("<u>alle</u>", "<u>all</u>"),
        ],
        "grammar/09 Verben/10 Unpersönliche Verben.html": [
            ("noch Zweifel.", "still doubts."),
        ],
        "grammar/10 Zeitformen und Modi/12 Subjonctif.html": [
            ("Indikativ", "indicative"),
            ("-Frage + indicative im", "-question + indicative in the"),
            ("wieder aufgenommen.", "taken up again."),
            ("(hoffen)", "(hope)"),
            ("(wünschen)", "(wish)"),
            ("(es scheint mir)", "(it seems to me)"),
            ("(es scheint)", "(it seems)"),
            ("(verstehen)", "(understand)"),
            ("(sagen)", "(say)"),
            ("(hören)", "(hear)"),
            ("(müssen)", "(must)"),
            ("(es ist notwendig / obligatorisch)", "(it is necessary / obligatory)"),
            ("(für notwendig halten)", "(consider necessary)"),
            ("(es kann sein)", "(it may be)"),
            ("(es ist möglich)", "(it is possible)"),
            ("(es besteht die Chance)", "(there is a chance)"),
            ("(es ist unmöglich)", "(it is impossible)"),
            ("(bezweifeln)", "(doubt)"),
            ("(es ist unwahrscheinlich)", "(it is unlikely)"),
            ("(sich freuen)", "(be pleased)"),
            ("(es freut mich)", "(it pleases me)"),
            ("(sich wundern)", "(be surprised)"),
            ("(überrascht sein)", "(be surprised)"),
            ("(es ist erstaunlich)", "(it is surprising)"),
            ("(traurig sein)", "(be sad)"),
            ("(unglücklich sein)", "(be unhappy)"),
            ("(bedauern)", "(regret)"),
            ("(es ist schade)", "(it is a pity)"),
            ("(befürchten)", "(fear)"),
            ("(Angst haben)", "(be afraid)"),
            ("„Verständnis haben“", "“be understanding”"),
        ],
        "grammar/99 Vokabeln/26 Bewegungsverben.html": [
            ("wieder hinaufsteigen", "climb up again"),
        ],
    }
    for rel, pairs in replacements.items():
        path = ROOT / rel
        text = path.read_text(encoding="utf-8")
        for old, new in pairs:
            text = text.replace(old, new)
        path.write_text(text, encoding="utf-8")


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
    repair_final_residuals()
    base.finalize_templates()
    base.validate_translation()
    base.sync_words()
    base.write_readme()
