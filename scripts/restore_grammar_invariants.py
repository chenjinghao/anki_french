#!/usr/bin/env python3
"""Restore French/IPA and known French-only structures from the clean baseline.

Learner-facing English translation may legitimately add presentation-only inline
markup inside answer text. The fail-closed validator remains the source of truth for
compatibility attributes/classes and legacy target counts.

Some original French material is not tagged `.fr`: notably conjugation tables,
spelling tokens in the pronunciation overview, and a small irregular auxiliary table
on the literary subjunctive page. Those source forms must never be machine-translated.

The module is dependency-free so combine/QA jobs do not need the ML runtime.
"""
from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

TOKEN_RE = re.compile(r"<!--.*?-->|<![^>]*>|<[^>]+>", re.S)
OPEN_RE = re.compile(r"^<\s*([A-Za-z][\w:-]*)\b")
CLOSE_RE = re.compile(r"^<\s*/\s*([A-Za-z][\w:-]*)\s*>")
CLASS_RE = re.compile(r"\bclass\s*=\s*([\"'])(.*?)\1", re.I | re.S)
VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}
PROTECTED = {"fr", "ipa"}
PRONUNCIATION_OVERVIEW = "grammar/02 Aussprache/1 Die Aussprache.html"
SUBJ_IMPARFAIT = "grammar/10 Zeitformen und Modi/13 Subjonctif imparfait.html"


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
    match = CLASS_RE.search(open_tag)
    return set(match.group(2).split()) if match else set()


def parse_elements(raw: str) -> list[Element]:
    elements: list[Element] = []
    stack: list[int] = []
    for match in TOKEN_RE.finditer(raw):
        token = match.group(0)
        if token.startswith("<!--") or token.startswith("<!") or token.startswith("<?"):
            continue
        closing = CLOSE_RE.match(token)
        if closing:
            tag = closing.group(1).lower()
            for pos in range(len(stack) - 1, -1, -1):
                if elements[stack[pos]].tag == tag:
                    idx = stack[pos]
                    elements[idx].close_start = match.start()
                    elements[idx].end = match.end()
                    del stack[pos:]
                    break
            continue
        opening = OPEN_RE.match(token)
        if not opening:
            continue
        tag = opening.group(1).lower()
        parent = stack[-1] if stack else None
        idx = len(elements)
        elements.append(Element(tag, match.start(), match.end(), token, parent))
        if parent is not None:
            elements[parent].children.append(idx)
        if token.rstrip().endswith("/>") or tag in VOID_TAGS:
            elements[idx].close_start = match.end()
            elements[idx].end = match.end()
        else:
            stack.append(idx)
    return elements


def baseline_text(commit: str, path: str) -> str:
    return subprocess.check_output(["git", "show", f"{commit}:{path}"], text=True)


def outer_protected(raw: str) -> list[Element]:
    elems = parse_elements(raw)
    selected: list[Element] = []
    for el in elems:
        if not (classes(el.open_tag) & PROTECTED) or el.close_start is None:
            continue
        parent = el.parent
        nested = False
        while parent is not None:
            if classes(elems[parent].open_tag) & PROTECTED:
                nested = True
                break
            parent = elems[parent].parent
        if not nested:
            selected.append(el)
    return selected


def elements_with_class(raw: str, class_name: str, tag: str | None = None) -> list[Element]:
    return [
        el for el in parse_elements(raw)
        if el.close_start is not None
        and class_name in classes(el.open_tag)
        and (tag is None or el.tag == tag)
    ]


def plain_tables(raw: str) -> list[Element]:
    return [
        el for el in parse_elements(raw)
        if el.tag == "table" and el.close_start is not None and not classes(el.open_tag)
    ]


def replace_bodies(now: str, before: str, current: list[Element], baseline: list[Element], label: str, path: str) -> str:
    sig_current = [(e.tag, tuple(sorted(classes(e.open_tag)))) for e in current]
    sig_baseline = [(e.tag, tuple(sorted(classes(e.open_tag)))) for e in baseline]
    if sig_current != sig_baseline:
        raise RuntimeError(f"{path}: {label} structure changed; refusing source restoration")
    replacements: list[tuple[int, int, str]] = []
    for cur, base in zip(current, baseline):
        assert cur.close_start is not None and base.close_start is not None
        replacements.append((cur.open_end, cur.close_start, base.body(before)))
    pieces: list[str] = []
    cursor = 0
    for start, end, value in sorted(replacements):
        pieces.append(now[cursor:start])
        pieces.append(value)
        cursor = end
    pieces.append(now[cursor:])
    return "".join(pieces)


def restore_protected(now: str, before: str, path: str) -> str:
    return replace_bodies(
        now, before, outer_protected(now), outer_protected(before), "protected FR/IPA", path
    )


def restore_french_only_structures(now: str, before: str, path: str) -> str:
    current_tables = elements_with_class(now, "section-conjugation-table", "table")
    baseline_tables = elements_with_class(before, "section-conjugation-table", "table")
    if current_tables or baseline_tables:
        now = replace_bodies(
            now, before, current_tables, baseline_tables, "French conjugation table", path
        )

    if path == PRONUNCIATION_OVERVIEW:
        current_tokens = elements_with_class(now, "rounded-border")
        baseline_tokens = elements_with_class(before, "rounded-border")
        now = replace_bodies(
            now, before, current_tokens, baseline_tokens, "pronunciation spelling token", path
        )

    if path == SUBJ_IMPARFAIT:
        current_plain = plain_tables(now)
        baseline_plain = plain_tables(before)
        now = replace_bodies(
            now, before, current_plain, baseline_plain, "irregular avoir/être source table", path
        )
    return now


def restore_page(path: Path, baseline: str) -> bool:
    rel = str(path)
    now = path.read_text(encoding="utf-8")
    before = baseline_text(baseline, rel)
    fixed = restore_protected(now, before, rel)
    fixed = restore_french_only_structures(fixed, before, rel)
    if fixed != now:
        path.write_text(fixed, encoding="utf-8")
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True)
    args = parser.parse_args()
    changed = 0
    for path in sorted(Path("grammar").rglob("*.html")):
        changed += int(restore_page(path, args.baseline))
    print(f"RESTORED PROTECTED/SOURCE GRAMMAR CONTENT: pages_changed={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
