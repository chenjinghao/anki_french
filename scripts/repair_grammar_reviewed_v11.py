#!/usr/bin/env python3
"""Compatibility-safe follow-up to reviewed semantic repairs.

The v10 wording improvements were correct but a few replacements introduced new
`.fr` wrapper spans around source forms that were plain text in the clean baseline.
Keep the improved English while removing only those newly-added wrappers.
"""
from __future__ import annotations

from pathlib import Path

R: dict[str, list[tuple[str, str]]] = {
    "14 Relativsätze/1 Relativsätze mit qui.html": [
        (
            '<p>French <span class="fr">qui</span> does not change for the gender or number of its antecedent; English usually translates it as “who,” “which,” or “that.”</p>',
            '<p>French qui does not change for the gender or number of its antecedent; English usually translates it as “who,” “which,” or “that.”</p>',
        ),
    ],
    "14 Relativsätze/2 Relativsätze mit que.html": [
        (
            '<p>French <span class="fr">que</span> likewise does not change for gender or number; English commonly translates it as “whom,” “which,” or “that,” and may sometimes omit it.</p>',
            '<p>French que likewise does not change for gender or number; English commonly translates it as “whom,” “which,” or “that,” and may sometimes omit it.</p>',
        ),
    ],
    "19 Inversion/1 Inversion mit Pronomen.html": [
        (
            '<p>If a verb ends in a vowel and is followed by <span class="fr">il</span>, <span class="fr">elle</span>, or <span class="fr">on</span>, insert <span class="fr">&#8209;t&#8209;</span> for pronunciation:</p>',
            '<p>If a verb ends in a vowel and is followed by <span class="fr">il</span>, <span class="fr">elle</span>, or <span class="fr">on</span>, insert &#8209;t&#8209; for pronunciation:</p>',
        ),
    ],
}


def main() -> int:
    changed = 0
    replacements = 0
    root = Path("grammar")
    for rel, rules in R.items():
        path = root / rel
        if not path.exists():
            continue
        raw = path.read_text(encoding="utf-8")
        new = raw
        count = 0
        for old, replacement in rules:
            n = new.count(old)
            if n > 1:
                raise RuntimeError(f"{rel}: reviewed-v11 anchor matched {n} times")
            if n == 1:
                new = new.replace(old, replacement, 1)
                count += 1
        if new != raw:
            path.write_text(new, encoding="utf-8")
            changed += 1
            replacements += count
            print(f"{rel}: reviewed-v11 replacements={count}")
    print(f"GRAMMAR REVIEWED REPAIRS V11: files={changed} replacements={replacements}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
