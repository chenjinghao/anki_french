#!/usr/bin/env python3
"""Repair known v4 residuals without touching French text or HTML attributes."""
from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAG_SPLIT_RE = re.compile(r"(<[^>]+>)")
OPEN_TAG_RE = re.compile(r"^<\s*([A-Za-z][\w:-]*)\b")
CLOSE_TAG_RE = re.compile(r"^<\s*/\s*([A-Za-z][\w:-]*)\s*>")
CLASS_RE = re.compile(r"\bclass\s*=\s*(['\"])(.*?)\1", re.I)

EXACT = {
    "Jahr": "year",
    "keine": "none",
    "schon wieder": "again",
    "weder ... noch": "neither ... nor",
    "Verwendung": "Usage",
    "Gebrauch": "Usage",
    "Geschlecht": "Gender",
    "Bildung": "Formation",
    "Morgen": "Morning",
}

PHRASES = {
    "Man verwendet": "One uses",
    "Man benutzt": "One uses",
    "Man braucht": "One needs",
    "verwendet man": "one uses",
    "Ludwig XIV. wurde im Jahr 1638 geboren.": "Louis XIV was born in 1638.",
    "Ort des Geschehens": "scene of the action",
    "im vollen Sinne des Wortes": "in the full sense of the word",
    "verschiedene Bedeutungen haben kann. Im Allgemeinen drückt es eine grobe, unhöfliche oder überaus lässige Handlung aus.": "can have different meanings. In general, it expresses a crude, impolite, or extremely casual action.",
    "die alle aus seiner Grundbedeutung": "all of which derive from its basic meaning",
    "abgeleitet sind. Diese Grundbedeutung entwickelte sich in verschiedene Kontexte, z.B. als „Partisan“ oder „Verfechter“,": "are derived from it. This basic meaning developed into different contexts, e.g. as “partisan” or “advocate”,",
    "(= Irgendwann im Laufe des Vormittags → Zeitspanne)": "(= at some point during the morning → time span)",
    "des Substantivs": "of the noun",
    "Mitglied des Teams": "member of the team",
    "Adverbien des Ortes": "Adverbs of place",
    "Wechsel des Hilfsverbs": "Change of auxiliary verb",
    "des Hauptverbs": "of the main verb",
    "+ Indikativ bedeutet hier „feststellen“, „begreifen“.": "+ indicative here means “to establish”, “to understand”.",
    "des Hilfsverbs": "of the auxiliary verb",
    "oft anstelle des": "often instead of the",
    "Umschreibung des": "paraphrase of the",
    "Hab keine Angst": "Don't be afraid",
    "anstelle des": "instead of the",
    "im (Monat), im Jahr": "in (month), in (year)",
    "angekommen war.": "had arrived.",
    "Es gibt keine(s).": "There is none.",
    "Man musste gehen.": "One had to leave.",
    "Du verstehst schon,": "You know,",
}


def repair_visible_text(text: str) -> str:
    parts = TAG_SPLIT_RE.split(text)
    stack: list[bool] = []
    for i, part in enumerate(parts):
        if not part:
            continue
        if part.startswith("<"):
            if part.startswith(("<!--", "<!", "<?")):
                continue
            if CLOSE_TAG_RE.match(part):
                if stack:
                    stack.pop()
                continue
            m = OPEN_TAG_RE.match(part)
            if m and not part.rstrip().endswith("/>"):
                tag = m.group(1).lower()
                classes = ""
                cm = CLASS_RE.search(part)
                if cm:
                    classes = cm.group(2)
                protected = any(c in {"fr", "ipa"} for c in classes.split()) or tag == "code"
                stack.append((stack[-1] if stack else False) or protected)
            continue
        if stack and stack[-1]:
            continue

        stripped = html.unescape(part).strip()
        if not stripped:
            continue
        leading = part[: len(part) - len(part.lstrip())]
        trailing = part[len(part.rstrip()) :]
        value = part.strip()
        decoded = html.unescape(value)
        if decoded in EXACT:
            parts[i] = leading + EXACT[decoded] + trailing
            continue
        for old, new in PHRASES.items():
            value = value.replace(old, new)
        parts[i] = leading + value + trailing
    return "".join(parts)


def repair_card(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    in_examples = False
    example_line = 0
    note_start: int | None = None
    note_end: int | None = None
    in_note = False

    for i, raw in enumerate(lines):
        newline = "\n" if raw.endswith("\n") else ""
        line = raw[:-1] if newline else raw
        stripped = line.strip()

        if line and not line.startswith(" "):
            if in_note and not stripped.startswith("Notiz:") and note_end is None:
                note_end = i
            in_examples = stripped.startswith("Beispielsätze:")
            in_note = stripped.startswith("Notiz:")
            if in_note:
                note_start = i + 1
            example_line = 0

        if in_examples:
            if not stripped:
                example_line = 0
                continue
            if line.startswith("  "):
                if example_line % 2 == 1:
                    value = line.strip()
                    if "**" in value or value.count("*") % 2:
                        value = value.replace("*", "")
                        indent = line[: len(line) - len(line.lstrip())]
                        lines[i] = indent + value + newline
                example_line += 1

    if in_note and note_start is not None and note_end is None:
        note_end = len(lines)
    if note_start is not None and note_end is not None and note_start < note_end:
        payload = "".join(lines[note_start:note_end])
        repaired = repair_visible_text(payload)
        replacement = repaired.splitlines(keepends=True)
        if len(replacement) == note_end - note_start:
            lines[note_start:note_end] = replacement

    path.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    for path in sorted((ROOT / "cards").glob("*.yml")):
        repair_card(path)
    for path in sorted((ROOT / "grammar").rglob("*.html")):
        text = path.read_text(encoding="utf-8")
        path.write_text(repair_visible_text(text), encoding="utf-8")


if __name__ == "__main__":
    main()
