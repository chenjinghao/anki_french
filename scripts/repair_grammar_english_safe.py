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
        raw = path.read_text(encoding="utf-8")
        new, n = apply_text_replacements(raw, PATH.get(rel, {}))
        if n:
            path.write_text(new, encoding="utf-8")
            total += n
            pages += 1
            print(f"{rel}: safely repaired text nodes={n}")
    print(f"GRAMMAR SAFE REVIEWED PROSE REPAIRS: pages={pages} text_nodes={total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
