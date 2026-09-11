#!/usr/bin/env python3
"""Translate plain learner-facing grammar targets from their nearest French source.

The grammar HTML intentionally keeps legacy `.de` classes for compatibility, but the
content of those elements is learner-facing and should be English. This pass covers
plain `.de` div/span/table-cell targets. Targets containing nested HTML are skipped
rather than rewritten wholesale, because they may contain IPA or pedagogical markup
that must remain byte-for-byte intact. Those exceptional targets are handled by the
reviewed prose/page repair layer.
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

NAME_REPAIRS = {
    "Marie": {"Mary": "Marie"},
    "Pierre": {"Peter": "Pierre"},
    "Jean": {"John": "Jean"},
    "Jacques": {"James": "Jacques"},
    "Michel": {"Michael": "Michel"},
    "François": {"Francis": "François", "French": "François"},
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


def plain(value: str) -> str:
    value = TAG_RE.sub("", value)
    value = html.unescape(value).replace("\u00a0", " ")
    return re.sub(r"\s+", " ", value).strip()


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


def collect_jobs(raw: str) -> tuple[list[tuple[LangElement, str, str | None]], int]:
    jobs: list[tuple[LangElement, str, str | None]] = []
    skipped_markup = 0
    last_fr: LangElement | None = None
    for el in elements(raw):
        if el.lang == "fr":
            if plain(el.body):
                last_fr = el
            continue
        if last_fr is None:
            continue
        distance = el.start - last_fr.end
        if distance < 0 or distance > MAX_PAIR_DISTANCE:
            continue
        source = plain(last_fr.body)
        if not source or not re.search(r"[A-Za-zÀ-ÿ]", source):
            continue
        # Never destroy nested markup such as <span class="ipa"> or <u>.
        # The reviewed repair layer handles these exceptional teaching targets.
        if TAG_RE.search(el.body):
            skipped_markup += 1
            continue
        jobs.append((el, source, source_lemma(last_fr)))
    return jobs, skipped_markup


def translate_page(path: Path, translator: CardTranslator, memory: dict[str, str]) -> tuple[int, int, int]:
    raw = path.read_text(encoding="utf-8")
    jobs, skipped_markup = collect_jobs(raw)
    if not jobs:
        return 0, 0, skipped_markup

    translated: list[str | None] = [None] * len(jobs)
    model_indices: list[int] = []
    model_sources: list[str] = []
    for i, (_target, source, lemma) in enumerate(jobs):
        if lemma and lemma in memory:
            translated[i] = memory[lemma]
        else:
            model_indices.append(i)
            model_sources.append(source)

    if model_sources:
        values = translator.translate_fr(model_sources)
        for idx, value in zip(model_indices, values):
            translated[idx] = preserve_names(jobs[idx][1], value)

    pieces: list[str] = []
    cursor = 0
    changes = 0
    for (target, _source, _lemma), value in zip(jobs, translated):
        assert value is not None
        current = plain(raw[target.body_start:target.body_end])
        replacement = html.escape(value.strip(), quote=False)
        pieces.append(raw[cursor:target.body_start])
        pieces.append(replacement)
        cursor = target.body_end
        if current != plain(replacement):
            changes += 1
    pieces.append(raw[cursor:])
    path.write_text("".join(pieces), encoding="utf-8")
    return len(jobs), changes, skipped_markup


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
    pairs = changes = skipped = 0
    for path in paths:
        p, c, s = translate_page(path, translator, memory)
        pairs += p
        changes += c
        skipped += s
        print(f"{path}: targets={p} changes={c} skipped_nested_markup={s}")
    print(
        f"GRAMMAR TARGET FR->EN SHARD {args.shard}/{args.shards}: "
        f"pages={len(paths)} targets={pairs} changes={changes} "
        f"skipped_nested_markup={skipped} lemma_memory={len(memory)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
