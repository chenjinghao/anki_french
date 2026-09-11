#!/usr/bin/env python3
"""Translate learner-facing grammar targets from their nearest French source.

Legacy `.de` classes are compatibility hooks; their displayed content should be
English. Plain targets and targets containing only pedagogical <u>/<br> markup are
translated from French. Sensitive nested markup (IPA spans, links, classes, data
attributes, etc.) is never rewritten wholesale. False-friend `.wrong` targets are
also excluded because they intentionally are not translations of the preceding French.
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
ELEMENT_RE = re.compile(
    r"<(?P<tag>div|span|td)\b"
    r"(?P<attrs>[^>]*\bclass\s*=\s*[\"'][^\"']*\b(?P<lang>fr|de)\b[^\"']*[\"'][^>]*)>"
    r"(?P<body>.*?)</(?P=tag)>",
    re.I | re.S,
)
WORD_RE = re.compile(r"^Wort:\s*(.*)$", re.M)
DEF_RE = re.compile(r"^Definition:\s*(.*)$", re.M)
MAX_PAIR_DISTANCE = 1800
SAFE_TARGET_TAGS = {"u", "br"}

NAME_REPAIRS = {
    "Marie": {"Mary": "Marie"},
    "Pierre": {"Peter": "Pierre"},
    "Jean": {"John": "Jean"},
    "Jacques": {"James": "Jacques"},
    "Michel": {"Michael": "Michel"},
    "François": {"French": "François"},
}


@dataclass
class LangElement:
    start: int
    end: int
    body_start: int
    body_end: int
    lang: str
    attrs: str
    body: str


@dataclass
class Job:
    target: LangElement
    source_plain: str
    source_body: str
    lemma: str | None


def plain(value: str) -> str:
    value = TAG_RE.sub("", value)
    value = html.unescape(value).replace("\u00a0", " ")
    return re.sub(r"\s+", " ", value).strip()


def norm_key(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value)).strip().casefold()


def classes(attrs: str) -> set[str]:
    m = CLASS_RE.search(attrs)
    return set(m.group(2).split()) if m else set()


def card_lemma_memory() -> dict[str, str]:
    """Map unambiguous French card headwords to reviewed English definitions."""
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


def elements(raw: str) -> list[LangElement]:
    out: list[LangElement] = []
    for m in ELEMENT_RE.finditer(raw):
        out.append(
            LangElement(
                start=m.start(),
                end=m.end(),
                body_start=m.start("body"),
                body_end=m.end("body"),
                lang=m.group("lang").lower(),
                attrs=m.group("attrs"),
                body=m.group("body"),
            )
        )
    return out


def source_lemma(el: LangElement) -> str | None:
    if "tag-lemma" not in classes(el.attrs):
        return None
    m = DATA_LEMMA_RE.search(el.attrs)
    if m:
        return html.unescape(m.group(2)).strip()
    return plain(el.body)


def safe_target_body(body: str) -> bool:
    """Allow only plain text and simple underline/line-break presentation markup."""
    tags = {m.group(1).lower() for m in TAG_NAME_RE.finditer(body)}
    if not tags:
        return True
    if not tags <= SAFE_TARGET_TAGS:
        return False
    # Only bare <u> and <br> markup is accepted. Attributes could carry semantics.
    for tag in TAG_RE.findall(body):
        low = tag.lower().strip()
        if low.startswith("<u") and low not in {"<u>", "</u>"}:
            return False
        if low.startswith("<br") and not re.fullmatch(r"<br\s*/?>", low, re.I):
            return False
    return True


def marked_segments(source_body: str) -> list[str]:
    """Turn French <u> highlights into *markers* and preserve <br> boundaries."""
    parts = BR_RE.split(source_body)
    out: list[str] = []
    for part in parts:
        def mark(m: re.Match[str]) -> str:
            inner = plain(m.group(1))
            return f"*{inner}*" if inner else ""
        marked = U_RE.sub(mark, part)
        marked = TAG_RE.sub("", marked)
        marked = html.unescape(marked).replace("\u00a0", " ")
        marked = re.sub(r"\s+", " ", marked).strip()
        out.append(marked)
    return out


def render_segment(value: str) -> str:
    escaped = html.escape(value.strip(), quote=False)
    return re.sub(r"\*([^*]+)\*", r"<u>\1</u>", escaped)


def collect_jobs(raw: str) -> tuple[list[Job], int, int]:
    jobs: list[Job] = []
    skipped_sensitive = 0
    skipped_wrong = 0
    last_fr: LangElement | None = None
    for el in elements(raw):
        if el.lang == "fr":
            if plain(el.body):
                last_fr = el
            continue
        if "wrong" in classes(el.attrs):
            skipped_wrong += 1
            continue
        if last_fr is None:
            continue
        distance = el.start - last_fr.end
        if distance < 0 or distance > MAX_PAIR_DISTANCE:
            continue
        source = plain(last_fr.body)
        if not source or not re.search(r"[A-Za-zÀ-ÿ]", source):
            continue
        if not safe_target_body(el.body):
            skipped_sensitive += 1
            continue
        lemma = source_lemma(last_fr)
        # Card definitions are useful only when the visible French target is exactly
        # the lemma. Multiword grammar phrases such as "à côté de" must be translated
        # as phrases, not replaced by the single-word definition of "côté".
        if lemma and norm_key(source) != norm_key(lemma):
            lemma = None
        jobs.append(Job(el, source, last_fr.body, lemma))
    return jobs, skipped_sensitive, skipped_wrong


def translate_page(
    path: Path, translator: CardTranslator, memory: dict[str, str]
) -> tuple[int, int, int, int]:
    raw = path.read_text(encoding="utf-8")
    jobs, skipped_sensitive, skipped_wrong = collect_jobs(raw)
    if not jobs:
        return 0, 0, skipped_sensitive, skipped_wrong

    translated: list[str | None] = [None] * len(jobs)
    segment_map: list[tuple[int, int, str]] = []
    model_segments: list[str] = []

    for i, job in enumerate(jobs):
        # Only plain, exact headwords use reviewed card-definition memory.
        if job.lemma and not TAG_RE.search(job.source_body) and job.lemma in memory:
            translated[i] = html.escape(memory[job.lemma].strip(), quote=False)
            continue
        segments = marked_segments(job.source_body)
        for seg_idx, segment in enumerate(segments):
            if segment:
                segment_map.append((i, seg_idx, segment))
                model_segments.append(segment)
        translated[i] = "\0".join([""] * len(segments))

    if model_segments:
        values = translator.translate_fr_with_emphasis(model_segments)
        rendered_by_job: dict[int, dict[int, str]] = {}
        for (job_idx, seg_idx, source_segment), value in zip(segment_map, values):
            fixed = preserve_names(source_segment.replace("*", ""), value)
            rendered_by_job.setdefault(job_idx, {})[seg_idx] = render_segment(fixed)
        for job_idx, job in enumerate(jobs):
            if job.lemma and not TAG_RE.search(job.source_body) and job.lemma in memory:
                continue
            source_segments = marked_segments(job.source_body)
            rendered = [rendered_by_job.get(job_idx, {}).get(i, "") for i in range(len(source_segments))]
            translated[job_idx] = "<br>".join(rendered)

    pieces: list[str] = []
    cursor = 0
    changes = 0
    for job, replacement in zip(jobs, translated):
        assert replacement is not None
        current = raw[job.target.body_start:job.target.body_end]
        pieces.append(raw[cursor:job.target.body_start])
        pieces.append(replacement)
        cursor = job.target.body_end
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
    pairs = changes = skipped = wrong = 0
    translator = CardTranslator(Path("."), batch_size=args.batch_size)
    for path in paths:
        p, c, s, w = translate_page(path, translator, memory)
        pairs += p
        changes += c
        skipped += s
        wrong += w
        print(
            f"{path}: targets={p} changes={c} "
            f"skipped_sensitive={s} skipped_wrong={w}"
        )
    print(
        f"GRAMMAR TARGET FR->EN SHARD {args.shard}/{args.shards}: "
        f"pages={len(paths)} targets={pairs} changes={changes} "
        f"skipped_sensitive={skipped} skipped_wrong={wrong} lemma_memory={len(memory)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
