#!/usr/bin/env python3
"""Translate grammar explanatory prose from clean German source with block context.

The old grammar conversion translated isolated HTML text nodes, which destroyed
sentence context around inline markup. This pass translates complete leaf blocks
(paragraphs, headings, list items, table cells, and leaf divs) while replacing HTML
markup with validated placeholders. French, legacy `.de` example targets, IPA, code,
and every original tag/attribute are restored byte-for-byte. If a model changes or
reorders a placeholder, that block is left in German so fail-closed QA can catch it.
"""
from __future__ import annotations

import argparse
import html
import re
from dataclasses import dataclass, field
from pathlib import Path

from translate_de_to_en_v6 import Translator, looks_german

TOKEN_RE = re.compile(r"<!--.*?-->|<![^>]*>|<[^>]+>", re.S)
OPEN_RE = re.compile(r"^<\s*([A-Za-z][\w:-]*)\b")
CLOSE_RE = re.compile(r"^<\s*/\s*([A-Za-z][\w:-]*)\s*>")
CLASS_RE = re.compile(r"\bclass\s*=\s*([\"'])(.*?)\1", re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")
MARKER_RE = re.compile(r"ZXQ(?:PH|O|C|V)\d{4}QXZ", re.I)
BLOCK_TAGS = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "th", "td", "div"}
DESC_BLOCK_TAGS = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "ul", "ol", "table", "thead", "tbody", "tr", "td", "th", "div"}
INLINE_TAGS = {"a", "b", "strong", "i", "em", "u", "span", "sup", "sub", "small", "mark", "abbr"}
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
PROTECTED_CLASSES = {"fr", "de", "ipa"}
SKIP_DIV_CLASSES = {"examples", "section-content"}


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
        return raw[self.open_end:self.close_start] if self.close_start is not None else ""


def classes(open_tag: str) -> set[str]:
    m = CLASS_RE.search(open_tag)
    return set(m.group(2).split()) if m else set()


def plain(value: str) -> str:
    value = TAG_RE.sub("", value)
    value = html.unescape(value).replace("\u00a0", " ")
    return re.sub(r"\s+", " ", value).strip()


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
            for pos in range(len(stack) - 1, -1, -1):
                if elements[stack[pos]].tag == tag:
                    idx = stack[pos]
                    elements[idx].close_start = m.start()
                    elements[idx].end = m.end()
                    del stack[pos:]
                    break
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


def protected(el: Element) -> bool:
    return el.tag == "code" or bool(classes(el.open_tag) & PROTECTED_CLASSES)


def has_protected_ancestor(idx: int, elems: list[Element]) -> bool:
    parent = elems[idx].parent
    while parent is not None:
        if protected(elems[parent]):
            return True
        parent = elems[parent].parent
    return False


def has_block_descendant(idx: int, elems: list[Element]) -> bool:
    todo = list(elems[idx].children)
    while todo:
        child_idx = todo.pop()
        child = elems[child_idx]
        if child.tag in DESC_BLOCK_TAGS:
            return True
        todo.extend(child.children)
    return False


def select_blocks(raw: str, elems: list[Element]) -> list[int]:
    selected: list[int] = []
    for idx, el in enumerate(elems):
        if el.tag not in BLOCK_TAGS or el.close_start is None or protected(el) or has_protected_ancestor(idx, elems):
            continue
        c = classes(el.open_tag)
        if el.tag == "div" and (c & SKIP_DIV_CLASSES):
            continue
        if has_block_descendant(idx, elems):
            continue
        text = plain(el.body(raw))
        if text and looks_german(text):
            selected.append(idx)
    return selected


def marker(kind: str, n: int) -> str:
    return f"ZXQ{kind}{n:04d}QXZ"


def encode_block(raw: str, idx: int, elems: list[Element]) -> tuple[str, dict[str, str], list[str]]:
    """Encode one selected block body with reversible structural placeholders."""
    el = elems[idx]
    assert el.close_start is not None
    replacements: list[tuple[int, int, str]] = []
    restore: dict[str, str] = {}
    order: list[str] = []
    counter = 0

    def next_marker(kind: str, raw_value: str) -> str:
        nonlocal counter
        m = marker(kind, counter)
        counter += 1
        restore[m] = raw_value
        order.append(m)
        return m

    def walk(child_idx: int) -> None:
        child = elems[child_idx]
        if child.end is None or child.close_start is None:
            return
        if protected(child):
            replacements.append((child.start, child.end, next_marker("PH", raw[child.start:child.end])))
            return
        if child.tag in INLINE_TAGS:
            replacements.append((child.start, child.open_end, next_marker("O", raw[child.start:child.open_end])))
            for grand in child.children:
                walk(grand)
            replacements.append((child.close_start, child.end, next_marker("C", raw[child.close_start:child.end])))
            return
        if child.tag in VOID_TAGS:
            replacements.append((child.start, child.end, next_marker("V", raw[child.start:child.end])))
            return
        # A selected leaf block should not contain an unhandled block descendant.
        replacements.append((child.start, child.end, next_marker("PH", raw[child.start:child.end])))

    for child_idx in el.children:
        walk(child_idx)

    body_start, body_end = el.open_end, el.close_start
    pieces: list[str] = []
    cursor = body_start
    for start, end, value in sorted(replacements):
        if start < cursor or start < body_start or end > body_end:
            continue
        pieces.append(html.unescape(raw[cursor:start]))
        pieces.append(f" {value} ")
        cursor = end
    pieces.append(html.unescape(raw[cursor:body_end]))
    encoded = re.sub(r"\s+", " ", "".join(pieces)).strip()
    return encoded, restore, order


def restore_block(translated: str, restore: dict[str, str], expected_order: list[str]) -> str | None:
    found = [m.upper() for m in MARKER_RE.findall(translated)]
    expected = [m.upper() for m in expected_order]
    if found != expected or any(translated.upper().count(m.upper()) != 1 for m in expected_order):
        return None

    # Split on placeholders so only translated text is HTML-escaped; original tags
    # and protected elements are restored exactly.
    canonical = translated
    for m in expected_order:
        canonical = re.sub(re.escape(m), m, canonical, flags=re.I)
    parts = re.split(f"({'|'.join(re.escape(m) for m in expected_order)})", canonical) if expected_order else [canonical]
    out: list[str] = []
    for part in parts:
        if part in restore:
            out.append(restore[part])
        else:
            out.append(html.escape(part, quote=False))
    value = "".join(out)
    value = re.sub(r"\s+(?=</(?:b|strong|i|em|u|span|a|sup|sub|small|mark|abbr)>)", "", value)
    value = re.sub(r"(?<=>(?:))\s+", " ", value) if False else value
    return value.strip()


def translate_page(path: Path, translator: Translator) -> tuple[int, int, int]:
    raw = path.read_text(encoding="utf-8")
    elems = parse_elements(raw)
    selected = select_blocks(raw, elems)
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
    failures = 0
    for (idx, restore, order), value in zip(metadata, translated):
        restored = restore_block(value, restore, order)
        if restored is None:
            failures += 1
            print(f"PLACEHOLDER FAIL {path}: {plain(elems[idx].body(raw))[:180]}")
            continue
        el = elems[idx]
        assert el.close_start is not None
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
    return len(encoded_jobs), changes, failures


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
    jobs = changes = failures = 0
    for path in pages:
        j, c, f = translate_page(path, translator)
        jobs += j
        changes += c
        failures += f
        print(f"{path}: prose_blocks={j} changes={c} placeholder_failures={f}")
    print(
        f"GRAMMAR PROSE DE->EN SHARD {args.shard}/{args.shards}: pages={len(pages)} "
        f"blocks={jobs} changes={changes} placeholder_failures={failures}"
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
