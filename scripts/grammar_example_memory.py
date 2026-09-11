#!/usr/bin/env python3
"""Reuse reviewed card French→English examples in grammar pages.

The script is conservative: it only changes a grammar target when the normalized French
sentence has one unambiguous English translation in the card corpus.  It preserves the
legacy `.de` class because that class is an internal deck compatibility hook.
"""
from __future__ import annotations

import argparse
import html
import re
from collections import defaultdict
from pathlib import Path

PAIR_RE = re.compile(
    r'(<div\s+class=["\']fr["\'][^>]*>)(.*?)(</div>\s*)(<div\s+class=["\']de\s+spoiler["\'][^>]*>)(.*?)(</div>)',
    re.I | re.S,
)
TAG_RE = re.compile(r'<[^>]+>')
STAR_RE = re.compile(r'\*')


def plain(s: str) -> str:
    s = TAG_RE.sub('', s)
    s = STAR_RE.sub('', s)
    s = html.unescape(s)
    s = s.replace('\u2019', "'").replace('\u00a0', ' ')
    return re.sub(r'\s+', ' ', s).strip()


def card_pairs(path: Path):
    lines = path.read_text(encoding='utf-8').splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.startswith('Beispielsätze:')) + 1
    except StopIteration:
        return
    body=[]
    for line in lines[start:]:
        if line and not line.startswith((' ', '\t')) and ':' in line:
            break
        if not line.strip():
            continue
        body.append(line.strip())
    for i in range(0, len(body)-1, 2):
        fr, en = body[i], body[i+1]
        if fr and en:
            yield plain(fr), en.strip()


def build_memory() -> tuple[dict[str, str], int]:
    choices: dict[str, set[str]] = defaultdict(set)
    for path in Path('cards').glob('*.yml'):
        for fr, en in card_pairs(path) or ():
            choices[fr].add(en)
    memory={fr: next(iter(ens)) for fr, ens in choices.items() if len(ens)==1}
    conflicts=sum(1 for ens in choices.values() if len(ens)>1)
    return memory, conflicts


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--report', default='grammar-example-memory.txt')
    args=ap.parse_args()
    memory, conflicts=build_memory()
    total=matched=changed=0
    unmatched=[]
    changed_rows=[]
    for path in sorted(Path('grammar').rglob('*.html')):
        raw=path.read_text(encoding='utf-8')
        local_changed=0
        def repl(m: re.Match[str]) -> str:
            nonlocal total, matched, changed, local_changed
            total += 1
            key=plain(m.group(2))
            en=memory.get(key)
            if en is None:
                unmatched.append((str(path), key, plain(m.group(5))))
                return m.group(0)
            matched += 1
            current=plain(m.group(5))
            # Card translations use *...* emphasis.  Grammar pages already emphasize
            # the French focus; keep the English target plain to avoid adding new HTML.
            clean_en=html.escape(en.replace('*',''), quote=False)
            if current == plain(clean_en):
                return m.group(0)
            changed += 1
            local_changed += 1
            changed_rows.append((str(path), key, current, plain(clean_en)))
            return ''.join((m.group(1),m.group(2),m.group(3),m.group(4),clean_en,m.group(6)))
        new=PAIR_RE.sub(repl,raw)
        if args.apply and local_changed:
            path.write_text(new,encoding='utf-8')
    lines=[
        'GRAMMAR EXAMPLE TRANSLATION MEMORY',
        f'Unique card translations: {len(memory)}',
        f'Conflicting card keys skipped: {conflicts}',
        f'Grammar French/target pairs found by strict wrapper regex: {total}',
        f'Matched unambiguously: {matched}',
        f'Would change/currently changed: {changed}',
        f'Unmatched: {len(unmatched)}',
        '', 'CHANGES',
    ]
    for path,fr,old,en in changed_rows:
        lines += [f'[{path}]',f'FR: {fr}',f'OLD: {old}',f'EN: {en}','']
    lines += ['UNMATCHED']
    for path,fr,old in unmatched:
        lines += [f'[{path}]',f'FR: {fr}',f'CURRENT: {old}','']
    Path(args.report).write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(f'Grammar pairs: {total}; matched: {matched}; changes: {changed}; unmatched: {len(unmatched)}')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
