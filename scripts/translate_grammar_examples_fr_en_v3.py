#!/usr/bin/env python3
"""Translate structurally adjacent French grammar targets without regex cross-pairing.

The grammar pages intentionally keep legacy `.de` classes for compatibility. This
translator changes only learner-facing text inside a target element whose immediately
preceding sibling is a `.fr` element under the same HTML parent. A small tokenizer
tracks real element boundaries, so nested spans/divs cannot cause a source to drift
across sections. French source text, IPA markup, attributes, IDs, and grammar links are
never rewritten.
"""
from __future__ import annotations

import argparse
import html
import re
from dataclasses import dataclass, field
from pathlib import Path

try:
    from .translate_cards_fr_en_v6 import CardTranslator
except ImportError:
    from translate_cards_fr_en_v6 import CardTranslator

TAG_RE = re.compile(r"<[^>]+>")
TOKEN_RE = re.compile(r"<!--.*?-->|<![^>]*>|<[^>]+>", re.S)
OPEN_RE = re.compile(r"^<\s*([A-Za-z][\w:-]*)\b")
CLOSE_RE = re.compile(r"^<\s*/\s*([A-Za-z][\w:-]*)\s*>")
CLASS_RE = re.compile(r"\bclass\s*=\s*([\"'])(.*?)\1", re.I | re.S)
DATA_LEMMA_RE = re.compile(r"\bdata-lemma\s*=\s*([\"'])(.*?)\1", re.I | re.S)
BR_RE = re.compile(r"<br\s*/?>", re.I)
U_RE = re.compile(r"<u\b[^>]*>(.*?)</u>", re.I | re.S)
WORD_RE = re.compile(r"^Wort:\s*(.*)$", re.M)
DEF_RE = re.compile(r"^Definition:\s*(.*)$", re.M)
GAP_RE = re.compile(r"(?:(?:\s+)|&ensp;|&nbsp;)*\Z", re.I)
SAFE_TARGET_TAGS = {"u", "br"}
PAIR_TAGS = {"div", "td", "span"}
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
MAX_SPAN_SOURCE_CHARS = 140

NAME_REPAIRS = {
    "Marie": {"Mary": "Marie"},
    "Pierre": {"Peter": "Pierre"},
    "Jean": {"John": "Jean"},
    "Jacques": {"James": "Jacques"},
    "Michel": {"Michael": "Michel"},
    "François": {"French": "François", "Francis": "François"},
}


@dataclass
class Element:
    tag: str
    start: int
    open_end: int
    open_tag: str
    parent: int | None
    close_start: int | None = None
    end: int | None = None
    children: list[int] = field(default_factory=list)

    def body(self, raw: str) -> str:
        if self.close_start is None:
            return ""
        return raw[self.open_end:self.close_start]


@dataclass
class Job:
    start: int
    end: int
    source_body: str
    source_plain: str
    lemma: str | None


def classes(open_tag: str) -> set[str]:
    m = CLASS_RE.search(open_tag)
    return set(m.group(2).split()) if m else set()


def plain(value: str) -> str:
    value = TAG_RE.sub("", value)
    value = html.unescape(value).replace("\u00a0", " ")
    return re.sub(r"\s+", " ", value).strip()


def norm_key(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value)).strip().casefold()


def parse_elements(raw: str) -> list[Element]:
    elements: list[Element] = []
    stack: list[int] = []

    for m in TOKEN_RE.finditer(raw):
        token = m.group(0)
        if token.startswith("<!--") or token.startswith("<!") or token.startswith("<?"):
            continue
        cm = CLOSE_RE.match(token)
        if cm:
            tag = cm.group(1).lower()
            match_pos = None
            for pos in range(len(stack) - 1, -1, -1):
                if elements[stack[pos]].tag == tag:
                    match_pos = pos
                    break
            if match_pos is None:
                continue
            idx = stack[match_pos]
            elements[idx].close_start = m.start()
            elements[idx].end = m.end()
            del stack[match_pos:]
            continue

        om = OPEN_RE.match(token)
        if not om:
            continue
        tag = om.group(1).lower()
        parent = stack[-1] if stack else None
        idx = len(elements)
        elements.append(Element(tag, m.start(), m.end(), token, parent))
        if parent is not None:
            elements[parent].children.append(idx)
        if token.rstrip().endswith("/>") or tag in VOID_TAGS:
            elements[idx].close_start = m.end()
            elements[idx].end = m.end()
        else:
            stack.append(idx)
    return elements


def safe_target_body(body: str) -> bool:
    tags = []
    for token in TAG_RE.findall(body):
        cm = CLOSE_RE.match(token)
        om = OPEN_RE.match(token)
        tag = (cm or om).group(1).lower() if (cm or om) else ""
        if tag:
            tags.append(tag)
        low = token.strip().lower()
        if tag == "u" and low not in {"<u>", "</u>"}:
            return False
        if tag == "br" and not re.fullmatch(r"<br\s*/?>", low, re.I):
            return False
    return set(tags) <= SAFE_TARGET_TAGS


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


def source_lemma(source: Element, source_text: str, memory: dict[str, str]) -> str | None:
    if "tag-lemma" not in classes(source.open_tag):
        return None
    m = DATA_LEMMA_RE.search(source.open_tag)
    if m:
        candidate = html.unescape(m.group(2)).strip()
        if norm_key(candidate) == norm_key(source_text) and candidate in memory:
            return candidate
    # When the displayed tag itself exactly matches a card headword, it is safe to
    # reuse that reviewed definition. Never collapse a multiword phrase to a shorter
    # data-lemma such as `à côté de` -> `côté`.
    return source_text if source_text in memory else None


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
            gap = raw[source.end:target.start]
            if not GAP_RE.fullmatch(gap):
                continue
            if "wrong" in classes(target.open_tag):
                skipped_wrong += 1
                continue

            source_body = source.body(raw)
            target_body = target.body(raw)
            source_text = plain(source_body)
            if not source_text or not re.search(r"[A-Za-zÀ-ÿ]", source_text):
                continue
            if source.tag == "span" and len(source_text) > MAX_SPAN_SOURCE_CHARS:
                skipped_long_span += 1
                continue
            if not safe_target_body(target_body):
                skipped_sensitive += 1
                continue
            jobs.append(Job(
                start=target.open_end,
                end=target.close_start,
                source_body=source_body,
                source_plain=source_text,
                lemma=source_lemma(source, source_text, memory),
            ))
    return sorted(jobs, key=lambda j: j.start), skipped_sensitive, skipped_wrong, skipped_long_span


def translate_page(path: Path, translator: CardTranslator, memory: dict[str, str]) -> tuple[int, int, int, int, int]:
    raw = path.read_text(encoding="utf-8")
    jobs, skipped_sensitive, skipped_wrong, skipped_long = collect_jobs(raw, memory)
    if not jobs:
        return 0, 0, skipped_sensitive, skipped_wrong, skipped_long

    translated: list[str | None] = [None] * len(jobs)
    segment_map: list[tuple[int, int, str]] = []
    model_segments: list[str] = []

    for i, job in enumerate(jobs):
        if job.lemma and not TAG_RE.search(job.source_body):
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
    return len(jobs), changes, skipped_sensitive, skipped_wrong, skipped_long


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

    paths = page_paths(args.shard, args.shards)
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
        f"GRAMMAR DOM-ADJACENT FR->EN SHARD {args.shard}/{args.shards}: "
        f"pages={len(paths)} pairs={pairs} changes={changes} "
        f"skipped_sensitive={sensitive} skipped_wrong={wrong} "
        f"skipped_long_span={long_span} lemma_memory={len(memory)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
