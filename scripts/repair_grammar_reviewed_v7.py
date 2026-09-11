#!/usr/bin/env python3
"""Small structural-safe reviewed repairs layered after v6."""
from __future__ import annotations

from pathlib import Path

PATH = Path("grammar/_/VerbenBringenMitnehmen.html")

REPLACEMENTS = [
    ("<div class=\"section-title\">Verbs of bringing and carrying</div>",
     "<div class=\"section-title\">Bringing and taking verbs</div>"),
    ("<th>Importance</th>", "<th>Meaning</th>"),
    (
        '<td>The Commission shall adopt implementing acts in accordance with the procedure referred to in paragraph 1 of this Article.</td>\n        <td><b class="tag-lemma">emmener</b>',
        '<td>em-</td>\n        <td><b class="tag-lemma">emmener</b>',
    ),
    (
        '<td>The Commission shall adopt implementing acts in accordance with the procedure referred to in paragraph 1 of this Article.</td>\n        <td><b class="tag-lemma">ramener</b>',
        '<td>ra-</td>\n        <td><b class="tag-lemma">ramener</b>',
    ),
    ("<td>(a)</td>", "<td>a-</td>"),
    ("<span class=\"de\">'withdrawing'</span>", "<span class=\"de\">\"take along\"</span>"),
    ("<span class=\"de\">'bringing away'</span>", "<span class=\"de\">\"take away\"</span>"),
    ("<span class=\"de\">\"bring in\"</span>", "<span class=\"de\">\"bring/take to\"</span>"),
    ("<span class=\"de\">'bringing'</span>", "<span class=\"de\">\"bring here\"</span>"),
    ("<span class=\"de\">\"bringing back\"</span>", "<span class=\"de\">\"bring back\"</span>"),
    ("<span class=\"de\">\"bringing back\"</span>", "<span class=\"de\">\"bring along again\"</span>"),
    ("(Focus on departure)", "(focus on departure)"),
    ("(Focus on arrival)", "(focus on arrival)"),
]


def main() -> int:
    if not PATH.exists():
        print("GRAMMAR REVIEWED REPAIRS V7: target page absent in this shard")
        return 0
    raw = PATH.read_text(encoding="utf-8")
    new = raw
    changes = 0
    for old, replacement in REPLACEMENTS:
        if old in new:
            new = new.replace(old, replacement, 1)
            changes += 1
    if new != raw:
        PATH.write_text(new, encoding="utf-8")
    print(f"GRAMMAR REVIEWED REPAIRS V7: replacements={changes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
