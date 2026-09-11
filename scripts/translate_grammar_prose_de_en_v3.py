#!/usr/bin/env python3
"""Translate grammar prose from clean German source with fail-safe block fallback.

Primary translation is the v2 full-block placeholder approach. When NLLB damages a
placeholder, leaves German behind, or produces a known hallucination pattern, this
version falls back to translating only the unprotected text nodes inside that same
block. French, legacy `.de` example targets, IPA, code, tags, and attributes are kept
byte-for-byte during the fallback.
"""
from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

from translate_de_to_en_v6 import EXACT_NODE_REPLACEMENTS, Translator, is_french_fragment, looks_german
from translate_grammar_prose_de_en_v2 import (
    BLOCK_TAGS,
    CLOSE_RE,
    DESC_BLOCK_TAGS,
    OPEN_RE,
    PROTECTED_CLASSES,
    SKIP_DIV_CLASSES,
    VOID_TAGS,
    classes,
    encode_block,
    has_block_descendant,
    has_protected_ancestor,
    parse_elements,
    plain,
    protected,
    restore_block,
)

TAG_SPLIT_RE = re.compile(r"(<[^>]+>)", re.S)
BAD_OUTPUT_RE = re.compile(
    r"\b(?:European Parliament|Member States?|Official Journal|standing committee|"
    r"manufacture of|implementing acts?|delegated acts?|customs tariff|former yugoslav)\b",
    re.I,
)
# High-signal German words/labels that the generic detector can miss when they appear
# alone in table cells or around protected inline examples.
GERMAN_EXTRA_RE = re.compile(
    r"\b(?:Aussprache|Ausnahme(?:n)?|Beachte|Bezeichnet|Zweck|Mittel|Ursache|"
    r"Preisangabe|Fortbewegungsart|Materialangabe|Beweggrund|Grundzahl|Wortbildung|"
    r"zurückgeben|folgen|ergibt|ergeben|verwendet|gebildet|ausgesprochen|"
    r"männlich(?:e|en|er|es)?|weiblich(?:e|en|er|es)?|unbestimmt(?:e|en|er|es)?|"
    r"Adverbien|Adjektive|Substantiv(?:e)?|Präposition(?:en)?|Pronomen|Endung(?:en)?)\b",
    re.I,
)


def german_candidate(text: str) -> bool:
    value = html.unescape(text).strip()
    return bool(value and (looks_german(value) or GERMAN_EXTRA_RE.search(value)))


def unprotected_text_nodes(body: str) -> list[str]:
    """Return learner-facing text nodes outside fr/de/ipa/code protection."""
    parts = TAG_SPLIT_RE.split(body)
    stack: list[tuple[str, bool]] = []
    out: list[str] = []
    for part in parts:
        if not part:
            continue
        if part.startswith("<"):
            if part.startswith("<!--") or part.startswith("<!") or part.startswith("<?"):
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
            is_protected = inherited or tag == "code" or bool(classes(part) & PROTECTED_CLASSES)
            if not part.rstrip().endswith("/>") and tag not in VOID_TAGS:
                stack.append((tag, is_protected))
            continue
        if stack and stack[-1][1]:
            continue
        value = html.unescape(part).strip()
        if value:
            out.append(value)
    return out


def select_translatable_blocks(raw: str, elems) -> list[int]:
    """Select leaf blocks only when German exists outside protected descendants.

    This avoids sending pure vocabulary rows (whose German is entirely inside `.de`)
    to the prose model, while still translating explanatory prose that happens to
    contain inline `.fr`/`.de` examples.
    """
    selected: list[int] = []
    for idx, el in enumerate(elems):
        if el.tag not in BLOCK_TAGS or el.close_start is None or protected(el) or has_protected_ancestor(idx, elems):
            continue
        if el.tag == "div" and (classes(el.open_tag) & SKIP_DIV_CLASSES):
            continue
        if has_block_descendant(idx, elems):
            continue
        if any(german_candidate(text) for text in unprotected_text_nodes(el.body(raw))):
            selected.append(idx)
    return selected


def suspicious_translation(source_body: str, translated_body: str) -> bool:
    source_text = " ".join(unprotected_text_nodes(source_body))
    value = " ".join(unprotected_text_nodes(translated_body))
    if not value:
        return True
    if any(german_candidate(text) for text in unprotected_text_nodes(translated_body)) or BAD_OUTPUT_RE.search(value):
        return True
    if len(value) > max(320, int(3.5 * max(1, len(source_text)))):
        return True
    return False


def fallback_translate_body(translator: Translator, body: str) -> str:
    """Translate only unprotected German text nodes, preserving markup exactly."""
    parts = TAG_SPLIT_RE.split(body)
    stack: list[tuple[str, bool]] = []
    jobs: list[tuple[int, str, str, str]] = []

    for i, part in enumerate(parts):
        if not part:
            continue
        if part.startswith("<"):
            if part.startswith("<!--") or part.startswith("<!") or part.startswith("<?"):
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
            is_protected = inherited or tag == "code" or bool(classes(part) & PROTECTED_CLASSES)
            if not part.rstrip().endswith("/>") and tag not in VOID_TAGS:
                stack.append((tag, is_protected))
            continue

        if stack and stack[-1][1]:
            continue
        stripped = html.unescape(part).strip()
        if not stripped:
            continue
        if stripped in EXACT_NODE_REPLACEMENTS:
            leading = part[: len(part) - len(part.lstrip())]
            trailing = part[len(part.rstrip()) :]
            parts[i] = leading + html.escape(EXACT_NODE_REPLACEMENTS[stripped], quote=False) + trailing
            continue
        if is_french_fragment(stripped, translator.french_terms) or not german_candidate(stripped):
            continue
        leading = part[: len(part) - len(part.lstrip())]
        trailing = part[len(part.rstrip()) :]
        jobs.append((i, leading, trailing, stripped))

    values = translator.translate([job[3] for job in jobs])
    for (i, leading, trailing, _), value in zip(jobs, values):
        parts[i] = leading + html.escape(value.strip(), quote=False) + trailing
    return "".join(parts)


def translate_page(path: Path, translator: Translator) -> tuple[int, int, int]:
    raw = path.read_text(encoding="utf-8")
    elems = parse_elements(raw)
    selected = select_translatable_blocks(raw, elems)
    if not selected:
        return 0, 0, 0

    encoded_jobs: list[str] = []
    metadata: list[tuple[int, dict[str, str], list[str]]] = []
    for idx in selected:
        encoded, restore, order = encode_block(raw, idx, elems)
        if not encoded:
            continue
        encoded_jobs.append(encoded)
        metadata.append((idx, restore, order))

    translated = translator.translate(encoded_jobs)
    replacements: list[tuple[int, int, str]] = []
    unresolved = 0
    fallback_count = 0

    for (idx, restore, order), value in zip(metadata, translated):
        el = elems[idx]
        assert el.close_start is not None
        source_body = el.body(raw)
        restored = restore_block(value, restore, order)
        reason = None
        if restored is None:
            reason = "placeholder"
        elif suspicious_translation(source_body, restored):
            reason = "quality"

        if reason is not None:
            fallback_count += 1
            restored = fallback_translate_body(translator, source_body)
            if suspicious_translation(source_body, restored):
                unresolved += 1
                print(f"FALLBACK UNRESOLVED {path}: {plain(source_body)[:180]}")
            else:
                print(f"FALLBACK {reason.upper()} {path}: {plain(source_body)[:180]}")

        replacements.append((el.open_end, el.close_start, restored))

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
    path.write_text("".join(pieces), encoding="utf-8")
    print(f"{path}: fallback_blocks={fallback_count} unresolved={unresolved}")
    return len(encoded_jobs), changes, unresolved


def page_paths(shard: int, shards: int) -> list[Path]:
    paths = sorted(Path("grammar").rglob("*.html"))
    return [path for i, path in enumerate(paths) if i % shards == shard]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--shards", type=int, default=1)
    ap.add_argument("--batch-size", type=int, default=16)
    args = ap.parse_args()
    if not (0 <= args.shard < args.shards):
        raise SystemExit("invalid shard")

    translator = Translator(Path("."), batch_size=args.batch_size)
    pages = page_paths(args.shard, args.shards)
    jobs = changes = unresolved = 0
    for path in pages:
        j, c, u = translate_page(path, translator)
        jobs += j
        changes += c
        unresolved += u
    print(
        f"GRAMMAR PROSE DE->EN V3 SHARD {args.shard}/{args.shards}: pages={len(pages)} "
        f"blocks={jobs} changes={changes} unresolved={unresolved}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
