#!/usr/bin/env python3
"""Restore protected French/IPA content from the clean source baseline.

Learner-facing English translation may legitimately add presentation-only inline
markup inside answer text (for example, <u> emphasis copied from the French source).
Those additions are not compatibility invariants.  The fail-closed validator is the
source of truth for compatibility attributes/classes and target-span counts.

This helper therefore restores only content that must never be translated: the inner
HTML of outermost `.fr` and `.ipa` elements.  It deliberately does not rewrite all
opening tags, because doing so incorrectly rejects harmless answer-side emphasis.
The protected element sequence itself must still match the baseline exactly.

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


def restore_protected(now: str, before: str, path: str) -> str:
    current = outer_protected(now)
    baseline = outer_protected(before)
    sig_current = [(e.tag, tuple(sorted(classes(e.open_tag)))) for e in current]
    sig_baseline = [(e.tag, tuple(sorted(classes(e.open_tag)))) for e in baseline]
    if sig_current != sig_baseline:
        raise RuntimeError(
            f"{path}: protected FR/IPA structure changed; refusing protected-content restoration"
        )

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


def restore_page(path: Path, baseline: str) -> bool:
    rel = str(path)
    now = path.read_text(encoding="utf-8")
    before = baseline_text(baseline, rel)
    fixed = restore_protected(now, before, rel)
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
    print(f"RESTORED PROTECTED GRAMMAR CONTENT: pages_changed={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
