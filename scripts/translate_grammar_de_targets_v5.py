#!/usr/bin/env python3
"""Translate every legacy German target element, not only adjacent FR/DE pairs.

The original deck uses the `de` class as a compatibility hook in spans, cells and
examples. Earlier passes only translated adjacent sibling pairs, leaving hundreds
of German targets untouched. This pass translates every leaf `.de` element from the
clean German source while preserving its tags/attributes. On the false-friends page,
the first 43 `.de.wrong` entries are German meaning contrasts and are translated;
the later `.de.wrong` entries are already English false friends and are preserved.
"""
from __future__ import annotations

import html
import re
from pathlib import Path

from translate_de_to_en_v6 import Translator
from translate_grammar_examples_hybrid_v4 import collect_jobs
from translate_grammar_prose_de_en_v2 import (
    CLOSE_RE,
    OPEN_RE,
    TAG_RE,
    VOID_TAGS,
    classes,
    parse_elements,
)

TAG_SPLIT_RE = re.compile(r'(<[^>]+>)', re.S)
LETTER_RE = re.compile(r'[A-Za-zÀ-ÖØ-öø-ÿ]')
PROTECT_NESTED = {'fr', 'ipa'}
FALSE_FRIENDS = Path('grammar/99 Vokabeln/28 Falsche Freunde.html')
GERMAN_WRONG_COUNT = 43


def text_jobs(body: str) -> tuple[list[str], list[tuple[int, str, str]], list[str]]:
    """Return a tag-split body, translatable positions and source text chunks."""
    parts = TAG_SPLIT_RE.split(body)
    stack: list[tuple[str, bool]] = []
    jobs: list[tuple[int, str, str]] = []
    values: list[str] = []
    for i, part in enumerate(parts):
        if not part:
            continue
        if part.startswith('<'):
            cm = CLOSE_RE.match(part)
            if cm:
                tag = cm.group(1).lower()
                for pos in range(len(stack) - 1, -1, -1):
                    if stack[pos][0] == tag:
                        del stack[pos:]
                        break
                continue
            om = OPEN_RE.match(part)
            if not om:
                continue
            tag = om.group(1).lower()
            inherited = stack[-1][1] if stack else False
            protected = inherited or tag == 'code' or bool(classes(part) & PROTECT_NESTED)
            if not part.rstrip().endswith('/>') and tag not in VOID_TAGS:
                stack.append((tag, protected))
            continue
        if stack and stack[-1][1]:
            continue
        decoded = html.unescape(part)
        stripped = decoded.strip()
        if not stripped or not LETTER_RE.search(stripped):
            continue
        leading = part[: len(part) - len(part.lstrip())]
        trailing = part[len(part.rstrip()):]
        jobs.append((i, leading, trailing))
        values.append(stripped)
    return parts, jobs, values


def translate_body(translator: Translator, body: str) -> str:
    parts, jobs, values = text_jobs(body)
    if not values:
        return body
    translated = translator.translate(values)
    for (i, leading, trailing), value in zip(jobs, translated):
        parts[i] = leading + html.escape(value.strip(), quote=False) + trailing
    return ''.join(parts)


def selected_targets(path: Path, raw: str):
    elems = parse_elements(raw)
    # The hybrid FR->EN pass owns these exact target ranges. Do not pre-translate
    # them here or its German-first fallback would see English as German input.
    hybrid_ranges = {(job.start, job.end) for job in collect_jobs(raw, {})[0]}
    wrong_seen = 0
    selected = []
    for idx, el in enumerate(elems):
        if el.close_start is None or 'de' not in classes(el.open_tag):
            continue
        if any('de' in classes(elems[c].open_tag) for c in el.children):
            continue
        if (el.open_end, el.close_start) in hybrid_ranges:
            continue
        is_wrong = 'wrong' in classes(el.open_tag)
        if is_wrong:
            wrong_seen += 1
            if path != FALSE_FRIENDS or wrong_seen > GERMAN_WRONG_COUNT:
                continue
        body = el.body(raw)
        if TAG_RE.sub('', html.unescape(body)).strip():
            selected.append((idx, el))
    return selected


def translate_page(path: Path, translator: Translator) -> tuple[int, int]:
    raw = path.read_text(encoding='utf-8')
    targets = selected_targets(path, raw)
    replacements = []
    for _, el in targets:
        assert el.close_start is not None
        old = el.body(raw)
        new = translate_body(translator, old)
        replacements.append((el.open_end, el.close_start, new))

    pieces = []
    cursor = 0
    changes = 0
    for start, end, new in sorted(replacements):
        pieces.append(raw[cursor:start])
        pieces.append(new)
        if raw[start:end] != new:
            changes += 1
        cursor = end
    pieces.append(raw[cursor:])
    if replacements:
        path.write_text(''.join(pieces), encoding='utf-8')
    return len(targets), changes
