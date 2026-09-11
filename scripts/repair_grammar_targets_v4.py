#!/usr/bin/env python3
"""Stable reviewed grammar repairs keyed by preserved French source text.

Unlike model-output string patches, these repairs locate a legacy `.de` target only
when its immediately preceding sibling is the exact reviewed French source under the
same HTML parent. This makes lexical fixes deterministic across model reruns while
preserving all compatibility attributes and French source text.
"""
from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from pathlib import Path

TOKEN_RE = re.compile(r"<!--.*?-->|<![^>]*>|<[^>]+>", re.S)
OPEN_RE = re.compile(r"^<\s*([A-Za-z][\w:-]*)\b")
CLOSE_RE = re.compile(r"^<\s*/\s*([A-Za-z][\w:-]*)\s*>")
CLASS_RE = re.compile(r"\bclass\s*=\s*([\"'])(.*?)\1", re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")
GAP_RE = re.compile(r"(?:(?:\s+)|&ensp;|&nbsp;)*\Z", re.I)
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
PAIR_TAGS = {"div", "td", "span"}

GLOBAL_TARGETS = {
    "s'ensuivre": "to ensue; to follow",
    "découler": "to result; to follow from",
    "résulter": "to result; to follow from",
    "le bond": "jump; leap",
}

PATH_TARGETS: dict[str, dict[str, str]] = {
    "16 Prépositions/1 Prépositions des Ortes.html": {},  # guard against accidental typo use
    "16 Präpositionen/1 Präpositionen des Ortes.html": {
        "à côté de": "next to; beside",
        "à droite de": "to the right of",
        "à gauche de": "to the left of",
        "au bout de": "at the end of",
        "au fond de": "at the back of",
        "derrière": "behind",
        "devant": "in front of",
        "en face de": "opposite; across from",
        "loin de": "far from",
        "près de": "near; close to",
    },
}

EXACT_PAGE_REPLACEMENTS: dict[str, list[tuple[str, str]]] = {
    "07 Pronomen/02 Die unverbundenen Personalpronomen.html": [
        (") are used to emphasize a subject. In German there is no direct correspondence for this form.",
         ") are used for emphasis and in positions where unstressed subject or object pronouns cannot be used. English has no exact one-to-one equivalent as a separate pronoun class."),
        ("The unconnected personnel pronouns", "Stressed personal pronouns"),
    ],
    "16 Präpositionen/1 Präpositionen des Ortes.html": [
        ("Prepositions of the place", "Prepositions of place"),
    ],
    "99 Vokabeln/28 Falsche Freunde.html": [
        ("(Anleihe/Bindung)", "(financial bond / tie)"),
    ],
}


@dataclass
class Element:
    tag: str
    start: int
    open_end: int
    open_tag: str
    parent: int | None
    close_start: int | None = None
    end: int | None = None
    children: list[int] = field(default_factory=list)

    def body(self, raw: str) -> str:
        return raw[self.open_end:self.close_start] if self.close_start is not None else ""


def classes(open_tag: str) -> set[str]:
    m = CLASS_RE.search(open_tag)
    return set(m.group(2).split()) if m else set()


def plain(value: str) -> str:
    value = TAG_RE.sub("", value)
    value = html.unescape(value).replace("\u00a0", " ")
    return re.sub(r"\s+", " ", value).strip()


def parse_elements(raw: str) -> list[Element]:
    elements: list[Element] = []
    stack: list[int] = []
    for m in TOKEN_RE.finditer(raw):
        token = m.group(0)
        if token.startswith("<!--") or token.startswith("<!") or token.startswith("<?"):
            continue
        cm = CLOSE_RE.match(token)
        if cm:
            tag = cm.group(1).lower()
            for pos in range(len(stack) - 1, -1, -1):
                if elements[stack[pos]].tag == tag:
                    idx = stack[pos]
                    elements[idx].close_start = m.start()
                    elements[idx].end = m.end()
                    del stack[pos:]
                    break
            continue
        om = OPEN_RE.match(token)
        if not om:
            continue
        tag = om.group(1).lower()
        parent = stack[-1] if stack else None
        idx = len(elements)
        elements.append(Element(tag, m.start(), m.end(), token, parent))
        if parent is not None:
            elements[parent].children.append(idx)
        if token.rstrip().endswith("/>") or tag in VOID_TAGS:
            elements[idx].close_start = m.end()
            elements[idx].end = m.end()
        else:
            stack.append(idx)
    return elements


def source_keyed_replacements(raw: str, mapping: dict[str, str]) -> list[tuple[int, int, str]]:
    elems = parse_elements(raw)
    roots = [i for i, e in enumerate(elems) if e.parent is None]
    child_map: dict[int | None, list[int]] = {None: roots}
    child_map.update({i: e.children for i, e in enumerate(elems) if e.children})
    replacements: list[tuple[int, int, str]] = []
    for siblings in child_map.values():
        for left_idx, right_idx in zip(siblings, siblings[1:]):
            source, target = elems[left_idx], elems[right_idx]
            if source.tag not in PAIR_TAGS or target.tag != source.tag:
                continue
            if source.end is None or target.close_start is None:
                continue
            if "fr" not in classes(source.open_tag) or "de" not in classes(target.open_tag):
                continue
            if not GAP_RE.fullmatch(raw[source.end:target.start]):
                continue
            source_text = plain(source.body(raw))
            if source_text not in mapping:
                continue
            replacements.append((target.open_end, target.close_start, html.escape(mapping[source_text], quote=False)))
    return replacements


def apply(path: Path) -> int:
    rel = str(path.relative_to("grammar"))
    raw = path.read_text(encoding="utf-8")
    mapping = dict(GLOBAL_TARGETS)
    mapping.update(PATH_TARGETS.get(rel, {}))
    replacements = source_keyed_replacements(raw, mapping)
    pieces: list[str] = []
    cursor = 0
    changes = 0
    for start, end, value in sorted(replacements):
        pieces.append(raw[cursor:start])
        pieces.append(value)
        if raw[start:end] != value:
            changes += 1
        cursor = end
    pieces.append(raw[cursor:])
    new = "".join(pieces)
    for old, replacement in EXACT_PAGE_REPLACEMENTS.get(rel, []):
        if old in new:
            count = new.count(old)
            new = new.replace(old, replacement)
            changes += count
    if new != raw:
        path.write_text(new, encoding="utf-8")
    if changes:
        print(f"{rel}: reviewed-v4 replacements={changes}")
    return changes


def main() -> int:
    total = files = 0
    for path in sorted(Path("grammar").rglob("*.html")):
        count = apply(path)
        if count:
            files += 1
            total += count
    print(f"GRAMMAR SOURCE-KEYED REVIEWED REPAIRS V4: files={files} replacements={total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
