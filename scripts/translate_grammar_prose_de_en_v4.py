#!/usr/bin/env python3
"""Exhaustive clean-source German prose translation.

Unlike v3, this pass does not depend on a narrow German-language detector to decide
whether clean-source learner prose should be translated. The clean baseline is
German by construction; the only English inserted beforehand is the reviewed source
adaptation set, which is explicitly whitelisted. This closes the large class of
mixed German/English fragments left by short labels and table cells.
"""
from __future__ import annotations

import html
import re
from pathlib import Path

import translate_grammar_prose_de_en_v3 as base
from adapt_grammar_clean_source_en_v3 import merged_replacements
from translate_de_to_en_v6 import EXACT_NODE_REPLACEMENTS, Translator, is_french_fragment
from translate_grammar_prose_de_en_v2 import (
    BLOCK_TAGS,
    CLOSE_RE,
    OPEN_RE,
    PROTECTED_CLASSES,
    SKIP_DIV_CLASSES,
    VOID_TAGS,
    classes,
    has_block_descendant,
    has_protected_ancestor,
    parse_elements,
    plain,
    protected,
)

LETTER_RE = re.compile(r'[A-Za-zÀ-ÖØ-öø-ÿ]')
WS_RE = re.compile(r'\s+')


def norm(value: str) -> str:
    return WS_RE.sub(' ', html.unescape(value)).strip()


def reviewed_nodes() -> set[str]:
    out: set[str] = set()
    for rules in merged_replacements().values():
        for _, new in rules:
            for part in base.TAG_SPLIT_RE.split(new):
                if part and not part.startswith('<'):
                    value = norm(part)
                    if value:
                        out.add(value)
    return out


REVIEWED_NODES = reviewed_nodes()


def should_translate_node(text: str, translator: Translator) -> bool:
    value = norm(text)
    if not value or not LETTER_RE.search(value):
        return False
    if value in REVIEWED_NODES:
        return False
    if is_french_fragment(value, translator.french_terms):
        return False
    return True


def select_translatable_blocks(raw: str, elems, translator: Translator) -> list[int]:
    selected: list[int] = []
    for idx, el in enumerate(elems):
        if el.tag not in BLOCK_TAGS or el.close_start is None or protected(el) or has_protected_ancestor(idx, elems):
            continue
        if el.tag == 'div' and (classes(el.open_tag) & SKIP_DIV_CLASSES):
            continue
        if has_block_descendant(idx, elems):
            continue
        nodes = base.unprotected_text_nodes(el.body(raw))
        if any(should_translate_node(text, translator) for text in nodes):
            selected.append(idx)
    return selected


def force_translate_body(translator: Translator, body: str) -> str:
    parts = base.TAG_SPLIT_RE.split(body)
    stack: list[tuple[str, bool]] = []
    jobs: list[tuple[int, str, str, str]] = []
    for i, part in enumerate(parts):
        if not part:
            continue
        if part.startswith('<'):
            if part.startswith('<!--') or part.startswith('<!') or part.startswith('<?'):
                continue
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
            is_protected = inherited or tag == 'code' or bool(classes(part) & PROTECTED_CLASSES)
            if not part.rstrip().endswith('/>') and tag not in VOID_TAGS:
                stack.append((tag, is_protected))
            continue
        if stack and stack[-1][1]:
            continue
        stripped = norm(part)
        if not should_translate_node(stripped, translator):
            continue
        leading = part[: len(part) - len(part.lstrip())]
        trailing = part[len(part.rstrip()):]
        if stripped in EXACT_NODE_REPLACEMENTS:
            parts[i] = leading + html.escape(EXACT_NODE_REPLACEMENTS[stripped], quote=False) + trailing
        else:
            jobs.append((i, leading, trailing, stripped))
    values = translator.translate([j[3] for j in jobs]) if jobs else []
    for (i, leading, trailing, _), value in zip(jobs, values):
        parts[i] = leading + html.escape(value.strip(), quote=False) + trailing
    return ''.join(parts)


def suspicious_translation(source_body: str, translated_body: str) -> bool:
    src = norm(' '.join(base.unprotected_text_nodes(source_body)))
    out = norm(' '.join(base.unprotected_text_nodes(translated_body)))
    if not out:
        return True
    if base.BAD_OUTPUT_RE.search(out):
        return True
    if any(base.german_candidate(text) for text in base.unprotected_text_nodes(translated_body)):
        return True
    if len(src) >= 12 and src == out:
        return True
    if len(out) > max(320, int(3.5 * max(1, len(src)))):
        return True
    return False


def translate_page(path: Path, translator: Translator) -> tuple[int, int, int]:
    raw = path.read_text(encoding='utf-8')
    elems = parse_elements(raw)
    selected = select_translatable_blocks(raw, elems, translator)
    if not selected:
        return 0, 0, 0

    encoded_jobs = []
    metadata = []
    direct_replacements = []
    for idx in selected:
        el = elems[idx]
        source_body = el.body(raw)
        nodes = base.unprotected_text_nodes(source_body)
        if any(norm(n) in REVIEWED_NODES for n in nodes):
            assert el.close_start is not None
            direct_replacements.append((el.open_end, el.close_start, force_translate_body(translator, source_body)))
            continue
        encoded, restore, order = base.encode_block_safe(raw, idx, elems, translator)
        if encoded:
            encoded_jobs.append(encoded)
            metadata.append((idx, restore, order))

    translated = translator.translate(encoded_jobs) if encoded_jobs else []
    replacements = list(direct_replacements)
    unresolved = 0
    for (idx, restore, order), value in zip(metadata, translated):
        el = elems[idx]
        assert el.close_start is not None
        source_body = el.body(raw)
        restored = base.restore_block(value, restore, order)
        if restored is None or suspicious_translation(source_body, restored):
            restored = force_translate_body(translator, source_body)
            if suspicious_translation(source_body, restored):
                unresolved += 1
                print(f'EXHAUSTIVE FALLBACK UNRESOLVED {path}: {plain(source_body)[:180]}')
        replacements.append((el.open_end, el.close_start, restored))

    pieces = []
    cursor = 0
    changes = 0
    for start, end, value in sorted(replacements):
        pieces.append(raw[cursor:start])
        pieces.append(value)
        if raw[start:end] != value:
            changes += 1
        cursor = end
    pieces.append(raw[cursor:])
    path.write_text(''.join(pieces), encoding='utf-8')
    return len(selected), changes, unresolved
