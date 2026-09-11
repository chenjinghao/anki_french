#!/usr/bin/env python3
"""Translate structurally paired grammar examples/glosses from French to English.

Only adjacent French -> legacy target pairs are eligible. This prevents the cross-
section mispairing possible with nearest-neighbour heuristics. The `.de` class remains
unchanged for compatibility. Plain targets and targets containing only <u>/<br> markup
are rewritten; IPA/link/attribute-rich nested markup and `.wrong` false-friend targets
are left for reviewed page-specific handling.
"""
from __future__ import annotations

import argparse
import html
import re
from dataclasses import dataclass
from pathlib import Path

try:
    from .translate_cards_fr_en_v6 import CardTranslator
except ImportError:
    from translate_cards_fr_en_v6 import CardTranslator

TAG_RE = re.compile(r"<[^>]+>")
TAG_NAME_RE = re.compile(r"</?\s*([A-Za-z0-9:_-]+)\b[^>]*>")
BR_RE = re.compile(r"<br\s*/?>", re.I)
U_RE = re.compile(r"<u\b[^>]*>(.*?)</u>", re.I | re.S)
CLASS_RE = re.compile(r"\bclass\s*=\s*([\"'])(.*?)\1", re.I | re.S)
DATA_LEMMA_RE = re.compile(r"\bdata-lemma\s*=\s*([\"'])(.*?)\1", re.I | re.S)
WORD_RE = re.compile(r"^Wort:\s*(.*)$", re.M)
DEF_RE = re.compile(r"^Definition:\s*(.*)$", re.M)
SAFE_TARGET_TAGS = {"u", "br"}

BLOCK_RE = re.compile(
    r"(?P<fr_open><(?P<tag>div|td)\b[^>]*class=[\"'][^\"']*\bfr\b[^\"']*[\"'][^>]*>)"
    r"(?P<fr>.*?)(</(?P=tag)>\s*)"
    r"(?P<de_open><(?P<tag2>div|td)\b[^>]*class=[\"'][^\"']*\bde\b[^\"']*[\"'][^>]*>)"
    r"(?P<de>.*?)(</(?P=tag2)>)",
    re.I | re.S,
)
SPAN_RE = re.compile(
    r"(?P<fr_open><span\b[^>]*class=[\"'][^\"']*\bfr\b[^\"']*[\"'][^>]*>)"
    r"(?P<fr>.*?)(</span>(?:&ensp;|&nbsp;|\s)*)"
    r"(?P<de_open><span\b[^>]*class=[\"'][^\"']*\bde\b[^\"']*[\"'][^>]*>)"
    r"(?P<de>.*?)(</span>)",
    re.I | re.S,
)

NAME_REPAIRS = {
    "Marie": {"Mary": "Marie"},
    "Pierre": {"Peter": "Pierre"},
    "Jean": {"John": "Jean"},
    "Jacques": {"James": "Jacques"},
    "Michel": {"Michael": "Michel"},
    "François": {"French": "François"},
}


@dataclass
class Job:
    start: int
    end: int
    source_body: str
    source_plain: str
    lemma: str | None


def plain(value: str) -> str:
    value = TAG_RE.sub("", value)
    value = html.unescape(value).replace("\u00a0", " ")
    return re.sub(r"\s+", " ", value).strip()


def norm_key(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value)).strip().casefold()


def classes(open_tag: str) -> set[str]:
    m = CLASS_RE.search(open_tag)
    return set(m.group(2).split()) if m else set()


def card_lemma_memory() -> dict[str, str]:
    choices: dict[str, set[str]] = {}
    for path in Path("cards").glob("*.yml"):
        raw = path.read_text(encoding="utf-8")
        wm, dm = WORD_RE.search(raw), DEF_RE.search(raw)
        if not wm or not dm:
            continue
        word = wm.group(1).strip().strip("'\"")
        definition = dm.group(1).strip().strip("'\"")
        if not word or not definition or definition in {"|-", "|", ">-", ">"}:
            continue
        choices.setdefault(word, set()).add(definition)
    return {word: next(iter(values)) for word, values in choices.items() if len(values) == 1}


def preserve_names(source: str, value: str) -> str:
    for french, repairs in NAME_REPAIRS.items():
        if re.search(rf"\b{re.escape(french)}\b", source):
            for wrong, right in repairs.items():
                value = re.sub(rf"\b{re.escape(wrong)}\b", right, value)
    return value


def page_paths(shard: int, shards: int) -> list[Path]:
    paths = sorted(Path("grammar").rglob("*.html"))
    return [path for i, path in enumerate(paths) if i % shards == shard]


def safe_target_body(body: str) -> bool:
    tags = {m.group(1).lower() for m in TAG_NAME_RE.finditer(body)}
    if not tags:
        return True
    if not tags <= SAFE_TARGET_TAGS:
        return False
    for tag in TAG_RE.findall(body):
        low = tag.strip().lower()
        if low.startswith("<u") and low not in {"<u>", "</u>"}:
            return False
        if low.startswith("<br") and not re.fullmatch(r"<br\s*/?>", low, re.I):
            return False
    return True


def marked_segments(source_body: str) -> list[str]:
    parts = BR_RE.split(source_body)
    out: list[str] = []
    for part in parts:
        def mark(m: re.Match[str]) -> str:
            value = plain(m.group(1))
            return f"*{value}*" if value else ""
        marked = U_RE.sub(mark, part)
        marked = TAG_RE.sub("", marked)
        marked = html.unescape(marked).replace("\u00a0", " ")
        out.append(re.sub(r"\s+", " ", marked).strip())
    return out


def render_segment(value: str) -> str:
    escaped = html.escape(value.strip(), quote=False)
    return re.sub(r"\*([^*]+)\*", r"<u>\1</u>", escaped)


def collect_jobs(raw: str) -> tuple[list[Job], int, int]:
    jobs: list[Job] = []
    occupied: list[tuple[int, int]] = []
    skipped_sensitive = skipped_wrong = 0

    for pattern in (BLOCK_RE, SPAN_RE):
        for m in pattern.finditer(raw):
            start, end = m.start("de"), m.end("de")
            if any(not (end <= a or start >= b) for a, b in occupied):
                continue
            if "wrong" in classes(m.group("de_open")):
                skipped_wrong += 1
                continue
            source = plain(m.group("fr"))
            if not source or not re.search(r"[A-Za-zÀ-ÿ]", source):
                continue
            if not safe_target_body(m.group("de")):
                skipped_sensitive += 1
                continue

            lemma = None
            if "tag-lemma" in classes(m.group("fr_open")):
                lm = DATA_LEMMA_RE.search(m.group("fr_open"))
                if lm:
                    candidate = html.unescape(lm.group(2)).strip()
                    if norm_key(source) == norm_key(candidate):
                        lemma = candidate
            jobs.append(Job(start, end, m.group("fr"), source, lemma))
            occupied.append((start, end))

    return sorted(jobs, key=lambda j: j.start), skipped_sensitive, skipped_wrong


def translate_page(path: Path, translator: CardTranslator, memory: dict[str, str]) -> tuple[int, int, int, int]:
    raw = path.read_text(encoding="utf-8")
    jobs, skipped_sensitive, skipped_wrong = collect_jobs(raw)
    if not jobs:
        return 0, 0, skipped_sensitive, skipped_wrong

    translated: list[str | None] = [None] * len(jobs)
    segment_map: list[tuple[int, int, str]] = []
    model_segments: list[str] = []

    for i, job in enumerate(jobs):
        if job.lemma and not TAG_RE.search(job.source_body) and job.lemma in memory:
            translated[i] = html.escape(memory[job.lemma].strip(), quote=False)
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
    return len(jobs), changes, skipped_sensitive, skipped_wrong


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--shards", type=int, default=1)
    ap.add_argument("--batch-size", type=int, default=16)
    args = ap.parse_args()
    if not (0 <= args.shard < args.shards):
        raise SystemExit("invalid shard")

    paths = page_paths(args.shard, args.shards)
    memory = card_lemma_memory()
    translator = CardTranslator(Path("."), batch_size=args.batch_size)
    pairs = changes = skipped = wrong = 0
    for path in paths:
        p, c, s, w = translate_page(path, translator, memory)
        pairs += p
        changes += c
        skipped += s
        wrong += w
        print(f"{path}: pairs={p} changes={c} skipped_sensitive={s} skipped_wrong={w}")
    print(
        f"GRAMMAR ADJACENT FR->EN SHARD {args.shard}/{args.shards}: "
        f"pages={len(paths)} pairs={pairs} changes={changes} "
        f"skipped_sensitive={skipped} skipped_wrong={wrong} lemma_memory={len(memory)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
