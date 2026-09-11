#!/usr/bin/env python3
"""Translate adjacent grammar targets with reviewed memory and German-first fallbacks.

The DOM adjacency rules from v3 are retained. Reviewed card definitions still win.
For short vocabulary/gloss spans, the clean German target is translated in robust
batches and French is used only when the German result fails quality checks. Longer
example pairs continue to use French as the semantic source of truth.
"""
from __future__ import annotations

import argparse
import html
import re
from dataclasses import dataclass
from pathlib import Path

from translate_cards_fr_en_v6 import (
    BAD_GLOSS,
    CardTranslator,
    clean_definition_source,
    normalize_gloss,
    suspicious_gloss,
)
from translate_grammar_examples_fr_en_v3 import (
    BR_RE,
    GAP_RE,
    MAX_SPAN_SOURCE_CHARS,
    PAIR_TAGS,
    TAG_RE,
    card_lemma_memory,
    classes,
    marked_segments,
    parse_elements,
    plain,
    preserve_names,
    render_segment,
    safe_target_body,
    source_lemma,
)

SENTENCE_PUNCT_RE = re.compile(r"[.!?](?:\s|$)")


@dataclass
class Job:
    start: int
    end: int
    pair_tag: str
    source_body: str
    source_plain: str
    target_body: str
    target_plain: str
    lemma: str | None


def collect_jobs(raw: str, memory: dict[str, str]) -> tuple[list[Job], int, int, int]:
    elems = parse_elements(raw)
    roots = [i for i, e in enumerate(elems) if e.parent is None]
    children: dict[int | None, list[int]] = {None: roots}
    for i, e in enumerate(elems):
        if e.children:
            children[i] = e.children

    jobs: list[Job] = []
    skipped_sensitive = skipped_wrong = skipped_long_span = 0
    for siblings in children.values():
        for left_idx, right_idx in zip(siblings, siblings[1:]):
            source = elems[left_idx]
            target = elems[right_idx]
            if source.tag not in PAIR_TAGS or target.tag != source.tag:
                continue
            if source.end is None or target.close_start is None or target.end is None:
                continue
            if "fr" not in classes(source.open_tag) or "de" not in classes(target.open_tag):
                continue
            if not GAP_RE.fullmatch(raw[source.end:target.start]):
                continue
            if "wrong" in classes(target.open_tag):
                skipped_wrong += 1
                continue

            source_body = source.body(raw)
            target_body = target.body(raw)
            source_text = plain(source_body)
            target_text = plain(target_body)
            if not source_text or not re.search(r"[A-Za-zÀ-ÿ]", source_text):
                continue
            if source.tag == "span" and len(source_text) > MAX_SPAN_SOURCE_CHARS:
                skipped_long_span += 1
                continue
            if not safe_target_body(target_body):
                skipped_sensitive += 1
                continue
            jobs.append(
                Job(
                    start=target.open_end,
                    end=target.close_start,
                    pair_tag=source.tag,
                    source_body=source_body,
                    source_plain=source_text,
                    target_body=target_body,
                    target_plain=target_text,
                    lemma=source_lemma(source, source_text, memory),
                )
            )
    return sorted(jobs, key=lambda j: j.start), skipped_sensitive, skipped_wrong, skipped_long_span


def is_short_gloss(job: Job) -> bool:
    return (
        job.pair_tag == "span"
        and len(job.source_plain) <= 70
        and len(job.target_plain) <= 120
        and not SENTENCE_PUNCT_RE.search(job.source_plain)
        and not BR_RE.search(job.target_body)
        and "<u" not in job.target_body.lower()
    )


def batch_translate_glosses(translator: CardTranslator, jobs: list[Job], indexes: list[int]) -> dict[int, str]:
    if not indexes:
        return {}
    sources = [clean_definition_source(jobs[i].target_plain) for i in indexes]
    direct_raw = translator.de.translate(sources)
    direct = [normalize_gloss(v) for v in direct_raw]
    result: dict[int, str] = {}
    bad_positions: list[int] = []

    for pos, (src, value) in enumerate(zip(sources, direct)):
        if suspicious_gloss(src, value):
            bad_positions.append(pos)
        else:
            result[indexes[pos]] = value

    if bad_positions:
        framed = [f"Das französische Wort bedeutet: {sources[pos]}" for pos in bad_positions]
        contextual = [normalize_gloss(v) for v in translator.de.translate(framed)]
        still_bad: list[tuple[int, str]] = []
        for pos, value in zip(bad_positions, contextual):
            src = sources[pos]
            if suspicious_gloss(src, value):
                still_bad.append((pos, value))
            else:
                result[indexes[pos]] = value

        if still_bad:
            fr_sources = [jobs[indexes[pos]].source_plain for pos, _ in still_bad]
            fr_values = [normalize_gloss(v) for v in translator.translate_fr(fr_sources)]
            for (pos, contextual_value), fallback in zip(still_bad, fr_values):
                src = sources[pos]
                direct_value = direct[pos]
                chosen = fallback
                if suspicious_gloss(jobs[indexes[pos]].source_plain, chosen):
                    chosen = direct_value or contextual_value or src
                result[indexes[pos]] = chosen
    return result


def translate_page(path: Path, translator: CardTranslator, memory: dict[str, str]) -> tuple[int, int, int, int, int]:
    raw = path.read_text(encoding="utf-8")
    jobs, skipped_sensitive, skipped_wrong, skipped_long = collect_jobs(raw, memory)
    if not jobs:
        return 0, 0, skipped_sensitive, skipped_wrong, skipped_long

    translated: list[str | None] = [None] * len(jobs)

    for i, job in enumerate(jobs):
        if job.lemma and not TAG_RE.search(job.source_body):
            translated[i] = html.escape(memory[job.lemma].strip(), quote=False)

    gloss_indexes = [i for i, job in enumerate(jobs) if translated[i] is None and is_short_gloss(job)]
    for i, value in batch_translate_glosses(translator, jobs, gloss_indexes).items():
        translated[i] = html.escape(value, quote=False)

    segment_map: list[tuple[int, int, str]] = []
    model_segments: list[str] = []
    for i, job in enumerate(jobs):
        if translated[i] is not None:
            continue
        segments = marked_segments(job.source_body)
        for seg_idx, segment in enumerate(segments):
            if segment:
                segment_map.append((i, seg_idx, segment))
                model_segments.append(segment)

    if model_segments:
        values = translator.translate_fr_with_emphasis(model_segments)
        by_job: dict[int, dict[int, str]] = {}
        for (job_idx, seg_idx, source_segment), value in zip(segment_map, values):
            fixed = preserve_names(source_segment.replace("*", ""), value)
            if BAD_GLOSS.search(fixed) or len(fixed) > max(160, 5 * len(source_segment)):
                de_source = clean_definition_source(jobs[job_idx].target_plain)
                de_value = normalize_gloss(translator.de.translate([de_source])[0]) if de_source else fixed
                if de_value and not suspicious_gloss(de_source, de_value):
                    fixed = de_value
            by_job.setdefault(job_idx, {})[seg_idx] = render_segment(fixed)
        for job_idx, job in enumerate(jobs):
            if translated[job_idx] is not None:
                continue
            source_segments = marked_segments(job.source_body)
            translated[job_idx] = "<br>".join(
                by_job.get(job_idx, {}).get(i, "") for i in range(len(source_segments))
            )

    pieces: list[str] = []
    cursor = 0
    changes = 0
    for job, replacement in zip(jobs, translated):
        assert replacement is not None
        current = raw[job.start:job.end]
        pieces.append(raw[cursor:job.start])
        pieces.append(replacement)
        cursor = job.end
        if current != replacement:
            changes += 1
    pieces.append(raw[cursor:])
    path.write_text("".join(pieces), encoding="utf-8")
    return len(jobs), changes, skipped_sensitive, skipped_wrong, skipped_long


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--shards", type=int, default=1)
    ap.add_argument("--batch-size", type=int, default=16)
    args = ap.parse_args()
    if not (0 <= args.shard < args.shards):
        raise SystemExit("invalid shard")

    paths = sorted(Path("grammar").rglob("*.html"))
    paths = [path for i, path in enumerate(paths) if i % args.shards == args.shard]
    memory = card_lemma_memory()
    translator = CardTranslator(Path("."), batch_size=args.batch_size)
    pairs = changes = sensitive = wrong = long_span = 0
    for path in paths:
        p, c, s, w, l = translate_page(path, translator, memory)
        pairs += p
        changes += c
        sensitive += s
        wrong += w
        long_span += l
        print(f"{path}: pairs={p} changes={c} skipped_sensitive={s} skipped_wrong={w} skipped_long_span={l}")
    print(
        f"GRAMMAR HYBRID TARGET V4 SHARD {args.shard}/{args.shards}: pages={len(paths)} "
        f"pairs={pairs} changes={changes} skipped_sensitive={sensitive} "
        f"skipped_wrong={wrong} skipped_long_span={long_span} lemma_memory={len(memory)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
