#!/usr/bin/env python3
"""Restore compatibility markup and protected French/IPA content from baseline.

Translation is allowed to change learner-facing prose and legacy `.de` target text,
but never tags/attributes or French/IPA source material. This script copies every
opening tag from the clean baseline (same tag sequence required) and restores the
inner HTML of outermost `.fr`/`.ipa` elements. Any structural mismatch fails closed.
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from translate_grammar_prose_de_en_v2 import OPEN_RE, TOKEN_RE, classes, parse_elements

PROTECTED = {'fr', 'ipa'}


def baseline_text(commit: str, path: str) -> str:
    return subprocess.check_output(['git', 'show', f'{commit}:{path}'], text=True)


def opening_tokens(raw: str):
    out = []
    for m in TOKEN_RE.finditer(raw):
        token = m.group(0)
        om = OPEN_RE.match(token)
        if om:
            out.append((m.start(), m.end(), om.group(1).lower(), token))
    return out


def restore_open_tags(now: str, before: str, path: str) -> str:
    a = opening_tokens(now)
    b = opening_tokens(before)
    if len(a) != len(b) or [x[2] for x in a] != [x[2] for x in b]:
        raise RuntimeError(f'{path}: tag structure changed; refusing invariant restoration')
    pieces = []
    cursor = 0
    for (start, end, _, _), (_, _, _, base_token) in zip(a, b):
        pieces.append(now[cursor:start])
        pieces.append(base_token)
        cursor = end
    pieces.append(now[cursor:])
    return ''.join(pieces)


def outer_protected(raw: str):
    elems = parse_elements(raw)
    selected = []
    for el in elems:
        c = classes(el.open_tag)
        if not (c & PROTECTED) or el.close_start is None:
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
    a = outer_protected(now)
    b = outer_protected(before)
    sig_a = [(e.tag, tuple(sorted(classes(e.open_tag)))) for e in a]
    sig_b = [(e.tag, tuple(sorted(classes(e.open_tag)))) for e in b]
    if sig_a != sig_b:
        raise RuntimeError(f'{path}: protected FR/IPA structure changed; refusing restoration')
    replacements = []
    for cur, base in zip(a, b):
        assert cur.close_start is not None and base.close_start is not None
        replacements.append((cur.open_end, cur.close_start, base.body(before)))
    pieces = []
    cursor = 0
    for start, end, value in sorted(replacements):
        pieces.append(now[cursor:start])
        pieces.append(value)
        cursor = end
    pieces.append(now[cursor:])
    return ''.join(pieces)


def restore_page(path: Path, baseline: str) -> bool:
    rel = str(path)
    now = path.read_text(encoding='utf-8')
    before = baseline_text(baseline, rel)
    fixed = restore_open_tags(now, before, rel)
    fixed = restore_protected(fixed, before, rel)
    if fixed != now:
        path.write_text(fixed, encoding='utf-8')
        return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--baseline', required=True)
    args = ap.parse_args()
    changed = 0
    for path in sorted(Path('grammar').rglob('*.html')):
        changed += int(restore_page(path, args.baseline))
    print(f'RESTORED GRAMMAR INVARIANTS: pages_changed={changed}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
