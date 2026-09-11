#!/usr/bin/env python3
"""Translate grammar example/gloss targets from their preserved French source.

Only the inner content of legacy `.de` target elements is replaced.  The `.de` class,
all surrounding HTML, all French source markup, and all compatibility attributes stay
byte-for-byte unchanged.  Pages can be sharded for a read-only Actions pilot.
"""
from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

from translate_cards_fr_en_v6 import CardTranslator

TAG_RE = re.compile(r'<[^>]+>')
BLOCK_RE = re.compile(
    r'(<(?P<tag>div|td)\b[^>]*class=["\'][^"\']*\bfr\b[^"\']*["\'][^>]*>)'
    r'(?P<fr>.*?)(</(?P=tag)>\s*)'
    r'(<(?P<tag2>div|td)\b[^>]*class=["\'][^"\']*\bde\b[^"\']*["\'][^>]*>)'
    r'(?P<de>.*?)(</(?P=tag2)>)', re.I | re.S)
SPAN_RE = re.compile(
    r'(<span\b[^>]*class=["\'][^"\']*\bfr\b[^"\']*["\'][^>]*>)'
    r'(?P<fr>.*?)(</span>(?:&ensp;|&nbsp;|\s)*)'
    r'(<span\b[^>]*class=["\'][^"\']*\bde\b[^"\']*["\'][^>]*>)'
    r'(?P<de>.*?)(</span>)', re.I | re.S)
DATA_LEMMA_RE = re.compile(r'\bdata-lemma=["\']([^"\']+)["\']', re.I)
WORD_RE = re.compile(r'^Wort:\s*(.*)$', re.M)
DEF_RE = re.compile(r'^Definition:\s*(.*)$', re.M)

NAME_REPAIRS = {
    'Marie': {'Mary': 'Marie'},
    'Pierre': {'Peter': 'Pierre'},
    'Jean': {'John': 'Jean'},
    'Jacques': {'James': 'Jacques'},
    'Michel': {'Michael': 'Michel'},
}


def plain(value: str) -> str:
    value = TAG_RE.sub('', value)
    value = html.unescape(value).replace('\u00a0', ' ')
    return re.sub(r'\s+', ' ', value).strip()


def card_lemma_memory() -> dict[str, str]:
    """Map unambiguous French card headwords to their reviewed English definition."""
    choices: dict[str, set[str]] = {}
    for path in Path('cards').glob('*.yml'):
        raw = path.read_text(encoding='utf-8')
        wm, dm = WORD_RE.search(raw), DEF_RE.search(raw)
        if not wm or not dm:
            continue
        word = wm.group(1).strip().strip("'\"")
        definition = dm.group(1).strip().strip("'\"")
        if not word or not definition or definition in {'|-', '|', '>-', '>'}:
            continue
        choices.setdefault(word, set()).add(definition)
    return {k: next(iter(v)) for k, v in choices.items() if len(v) == 1}


def preserve_names(source: str, value: str) -> str:
    for french, repairs in NAME_REPAIRS.items():
        if re.search(rf'\b{re.escape(french)}\b', source):
            for wrong, right in repairs.items():
                value = re.sub(rf'\b{re.escape(wrong)}\b', right, value)
    return value


def page_paths(shard: int, shards: int) -> list[Path]:
    paths = sorted(Path('grammar').rglob('*.html'))
    return [p for i, p in enumerate(paths) if i % shards == shard]


def translate_page(path: Path, translator: CardTranslator, lemma_memory: dict[str, str]) -> tuple[int, int]:
    raw = path.read_text(encoding='utf-8')
    jobs: list[tuple[int, int, str, str | None]] = []
    occupied: list[tuple[int, int]] = []

    for pattern in (BLOCK_RE, SPAN_RE):
        for m in pattern.finditer(raw):
            start, end = m.start('de'), m.end('de')
            if any(not (end <= a or start >= b) for a, b in occupied):
                continue
            source = plain(m.group('fr'))
            if not source or not re.search(r'[A-Za-zÀ-ÿ]', source):
                continue
            opener = m.group(1)
            lemma = None
            if 'tag-lemma' in opener:
                lm = DATA_LEMMA_RE.search(opener)
                if lm:
                    lemma = html.unescape(lm.group(1)).strip()
            jobs.append((start, end, source, lemma))
            occupied.append((start, end))

    if not jobs:
        return 0, 0

    translated: list[str | None] = [None] * len(jobs)
    model_indices=[]
    model_sources=[]
    for i, (_, _, source, lemma) in enumerate(jobs):
        if lemma and lemma in lemma_memory:
            translated[i] = lemma_memory[lemma]
        else:
            model_indices.append(i)
            model_sources.append(source)
    if model_sources:
        for idx, value in zip(model_indices, translator.translate_fr(model_sources)):
            translated[idx] = preserve_names(jobs[idx][2], value)

    changes=0
    pieces=[]
    cursor=0
    for (start,end,source,_), value in sorted(zip(jobs, translated), key=lambda x: x[0][0]):
        assert value is not None
        current=plain(raw[start:end])
        target=html.escape(value.strip(), quote=False)
        pieces.append(raw[cursor:start])
        pieces.append(target)
        cursor=end
        if current != plain(target):
            changes += 1
    pieces.append(raw[cursor:])
    new=''.join(pieces)
    path.write_text(new, encoding='utf-8')
    return len(jobs), changes


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--shard', type=int, default=0)
    ap.add_argument('--shards', type=int, default=1)
    ap.add_argument('--batch-size', type=int, default=16)
    args=ap.parse_args()
    if not (0 <= args.shard < args.shards):
        raise SystemExit('invalid shard')
    paths=page_paths(args.shard,args.shards)
    memory=card_lemma_memory()
    translator=CardTranslator(Path('.'), batch_size=args.batch_size)
    pairs=changes=0
    for path in paths:
        p,c=translate_page(path,translator,memory)
        pairs += p; changes += c
        print(f'{path}: pairs={p} changes={c}')
    print(f'GRAMMAR FR->EN SHARD {args.shard}/{args.shards}: pages={len(paths)} pairs={pairs} changes={changes} lemma_memory={len(memory)}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
