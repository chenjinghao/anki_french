#!/usr/bin/env python3
"""Final compatibility-safe reviewed grammar repairs.

This layer only performs exact, path-scoped learner-facing text substitutions.  It
preserves the existing HTML tag structure so the clean-source French/IPA and
compatibility invariants remain unchanged.
"""
from __future__ import annotations

from pathlib import Path

R: dict[str, list[tuple[str, str]]] = {
    "07 Pronomen/08 Die Demonstrativpronomen.html": [
        (
            '<td rowspan="2">of a kind used for the manufacture of foodstuffs</td>',
            '<td rowspan="2">Masculine</td>',
        ),
    ],
    "07 Pronomen/09 Die Demonstrativbegleiter.html": [
        (
            '<td>of a kind used for the manufacture of foodstuffs</td>',
            '<td>Masculine</td>',
        ),
    ],
    "07 Pronomen/10 Die unbestimmten Demonstrativpronomen.html": [
        (
            '<td rowspan="2">of a kind used for the manufacture of foodstuffs</td>',
            '<td rowspan="2">Masculine</td>',
        ),
    ],
    "10 Zeitformen und Modi/10 Impératif.html": [
        (
            '<td>Second person singular</td>\n        <td>of a kind used for the manufacture of foodstuffs</td>',
            '<td>Second person singular</td>\n        <td>lave-toi</td>',
        ),
        (
            '<td>1 person plural</td>\n        <td>of a kind used for the manufacture of foodstuffs</td>',
            '<td>1 person plural</td>\n        <td>lavons-nous</td>',
        ),
    ],
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
    "99 Vokabeln/15 Arbeit und Wirtschaft.html": [
        (
            '<span class="de">Members of the European Parliament and of the Council</span>',
            '<span class="de">association; organization</span>',
        ),
    ],
    "99 Vokabeln/28 Falsche Freunde.html": [
        (
            '<span class="de wrong left-x">of a kind used for the manufacture of foodstuffs</span> (shrouded/disrespectful)',
            '<span class="de wrong left-x">brusque</span> (curt/rude)',
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
