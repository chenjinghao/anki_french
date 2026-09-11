#!/usr/bin/env python3
"""Apply reviewed grammar prose repairs without substring corruption.

This imports the explicit reviewed replacement tables from repair_grammar_english.py,
but applies every replacement with lexical boundaries whenever the replacement starts
or ends in a word character. That prevents short entries such as ``Bei``, ``den``,
``und``, ``oder`` or ``After a`` from changing text inside longer English words.
French/IPA/code/script/style text and all HTML tags/attributes remain untouched.
"""
from __future__ import annotations

import re
from pathlib import Path

from repair_grammar_english import CLASS, CLOSE, GLOBAL, OPEN, PATH, TAG_SPLIT, VOID

WORD_CHAR = r"A-Za-z0-9_À-ÖØ-öø-ÿ"

# High-confidence residuals found during the grammar-specific manual pass.
EXTRA_GLOBAL = {
    "Wochentage": "Days of the week",
    "Jahreszeiten": "Seasons",
    "Himmelsrichtungen": "Cardinal directions",
    "Sprachen": "Languages",
    "Transportmittel": "Means of transport",
    "Kontinente": "Continents",
    "transitiven Verben": "transitive verbs",
    "intransitiven Verben": "intransitive verbs",
    "reflexiven Verben": "reflexive verbs",
    "Passivformen": "passive forms",
    "intransitiv": "intransitive",
    "transitiv": "transitive",
}

EXTRA_PATH = {
    "09 Verben/07 Die Hilfsverben avoir und être.html": {
        "selbst": "themselves",
        "hinausgehen": "go out",
        "hinausbringen": "take out",
        "hinaufgehen": "go up",
        "hinaufbringen": "take up",
        "heimkommen": "come home",
        "hineinbringen": "bring in",
        "umdrehen": "turn over",
        "herabsteigen": "go down",
        "herunterbringen": "take down",
        "composite times": "compound tenses",
        "with some intransitive verbs of the movement": "with some intransitive verbs of motion",
    },
    "04 Substantive/01 Das Geschlecht der Substantive.html": {
        "The German neutrum does not exist. The sex can differ from the German": "French has no neuter grammatical gender. A noun’s gender does not necessarily match the gender of its English equivalent",
        "nouns should always be taught with their article and sex": "nouns should always be learned with their article and gender",
        "Males are usually:": "The following are usually masculine:",
        "Females are usually:": "The following are usually feminine:",
        "formerly exclusively male occupational names": "occupational nouns traditionally used only in the masculine",
        "For some nouns, the form is identical. Only the article shows the gender:": "For some nouns, the masculine and feminine forms are identical; only the article shows the gender:",
    },
}


def bounded_replace(value: str, old: str, new: str) -> str:
    """Replace a reviewed fragment only at safe lexical boundaries."""
    prefix = rf"(?<![{WORD_CHAR}])" if old and re.match(rf"[{WORD_CHAR}]", old[0]) else ""
    suffix = rf"(?![{WORD_CHAR}])" if old and re.match(rf"[{WORD_CHAR}]", old[-1]) else ""
    return re.sub(prefix + re.escape(old) + suffix, lambda _m: new, value)


def apply_text_replacements(raw: str, local: dict[str, str]) -> tuple[str, int]:
    parts = TAG_SPLIT.split(raw)
    stack: list[tuple[str, bool]] = []
    changes = 0
    mapping = dict(GLOBAL)
    mapping.update(EXTRA_GLOBAL)
    mapping.update(local)
    ordered = sorted(mapping.items(), key=lambda kv: len(kv[0]), reverse=True)

    for i, part in enumerate(parts):
        if not part:
            continue
        if part.startswith("<"):
            cm = CLOSE.fullmatch(part.strip())
            if cm:
                if stack:
                    stack.pop()
                continue
            om = OPEN.match(part)
            if om and not part.rstrip().endswith("/>"):
                tag = om.group(1).lower()
                attrs = om.group(2)
                cls = CLASS.search(attrs)
                classes = set(cls.group(2).split()) if cls else set()
                protected = (
                    (stack[-1][1] if stack else False)
                    or bool(classes & {"fr", "ipa"})
                    or tag in {"code", "script", "style"}
                )
                if tag not in VOID:
                    stack.append((tag, protected))
            continue
        if stack and stack[-1][1]:
            continue

        value = part
        for old, new in ordered:
            value = bounded_replace(value, old, new)
        if value != part:
            parts[i] = value
            changes += 1

    return "".join(parts), changes


def main() -> int:
    total = pages = 0
    for path in sorted(Path("grammar").rglob("*.html")):
        rel = str(path.relative_to("grammar"))
        local = dict(PATH.get(rel, {}))
        local.update(EXTRA_PATH.get(rel, {}))
        raw = path.read_text(encoding="utf-8")
        new, n = apply_text_replacements(raw, local)
        if n:
            path.write_text(new, encoding="utf-8")
            total += n
            pages += 1
            print(f"{rel}: safely repaired text nodes={n}")
    print(f"GRAMMAR SAFE REVIEWED PROSE REPAIRS: pages={pages} text_nodes={total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
