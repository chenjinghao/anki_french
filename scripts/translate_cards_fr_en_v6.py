#!/usr/bin/env python3
"""Card-only v6 translator using French as the source for example sentences.

French example sentences are the semantic source of truth. Definitions and notes
still originate in German, so they are translated German->English. Learner-facing
French lines and compatibility-sensitive YAML/HTML structure are preserved.
"""
from __future__ import annotations

import argparse
import html
import os
import re
import textwrap
from pathlib import Path
from typing import List

import torch
from transformers import AutoTokenizer

from translate_de_to_en_v6 import (
    CLASS_RE,
    CLOSE_TAG_RE,
    COMMENT_REPLACEMENTS,
    EMPH_RE,
    EXACT_NODE_REPLACEMENTS,
    MODEL_NAME,
    OPEN_TAG_RE,
    TAG_SPLIT_RE,
    TGT_LANG,
    Translator,
    find_and_mark,
    is_french_fragment,
)

FR_LANG = "fra_Latn"


class CardTranslator:
    def __init__(self, root: Path, batch_size: int = 16):
        self.batch_size = batch_size
        self.de = Translator(root=root, batch_size=batch_size)
        self.fr_tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, src_lang=FR_LANG)
        self.fr_target_id = self.fr_tokenizer.convert_tokens_to_ids(TGT_LANG)

    def translate_fr(self, texts: List[str]) -> List[str]:
        if not texts:
            return []
        out: List[str] = []
        for start in range(0, len(texts), self.batch_size):
            batch = texts[start : start + self.batch_size]
            encoded = self.fr_tokenizer(
                batch, return_tensors="pt", padding=True, truncation=True, max_length=512
            )
            with torch.inference_mode():
                generated = self.de.model.generate(
                    **encoded,
                    forced_bos_token_id=self.fr_target_id,
                    max_new_tokens=384,
                    num_beams=4,
                    no_repeat_ngram_size=4,
                    repetition_penalty=1.08,
                )
            out.extend(v.strip() for v in self.fr_tokenizer.batch_decode(generated, skip_special_tokens=True))
        return out

    def translate_fr_with_emphasis(self, texts: List[str]) -> List[str]:
        clean = [EMPH_RE.sub(lambda m: m.group(1), text) for text in texts]
        translated_full = self.translate_fr(clean)
        span_lists = [EMPH_RE.findall(text) for text in texts]
        flat_spans = [span for spans in span_lists for span in spans]
        translated_spans = self.translate_fr(flat_spans)
        cursor = 0
        out: List[str] = []
        for full, spans in zip(translated_full, span_lists):
            value = full
            for _ in spans:
                value = find_and_mark(value, translated_spans[cursor])
                cursor += 1
            value = re.sub(r"\*{2,}", "*", value)
            out.append(value)
        return out


def translate_note_markup(translator: CardTranslator, markup: str) -> str:
    """Translate all learner-facing note prose while protecting .fr/.ipa/code text."""
    parts = TAG_SPLIT_RE.split(markup)
    stack: list[tuple[str, bool]] = []
    jobs: list[tuple[int, str, str, str]] = []

    for i, part in enumerate(parts):
        if not part:
            continue
        if part.startswith("<"):
            if part.startswith("<!--") or part.startswith("<!") or part.startswith("<?"):
                continue
            if CLOSE_TAG_RE.match(part):
                if stack:
                    stack.pop()
                continue
            match = OPEN_TAG_RE.match(part)
            if match and not part.rstrip().endswith("/>"):
                tag = match.group(1).lower()
                classes = ""
                cm = CLASS_RE.search(part)
                if cm:
                    classes = cm.group(2)
                protected = any(c in {"fr", "ipa"} for c in classes.split()) or tag == "code"
                stack.append((tag, (stack[-1][1] if stack else False) or protected))
            continue

        if stack and stack[-1][1]:
            continue
        stripped = html.unescape(part).strip()
        if not stripped or not re.search(r"[A-Za-zÀ-ÖØ-öø-ÿÄÖÜäöüß]", stripped):
            continue
        if stripped in EXACT_NODE_REPLACEMENTS:
            leading = part[: len(part) - len(part.lstrip())]
            trailing = part[len(part.rstrip()) :]
            parts[i] = leading + EXACT_NODE_REPLACEMENTS[stripped] + trailing
            continue
        if is_french_fragment(stripped, translator.de.french_terms):
            continue
        leading = part[: len(part) - len(part.lstrip())]
        trailing = part[len(part.rstrip()) :]
        jobs.append((i, leading, trailing, part.strip()))

    translated = translator.de.translate([job[3] for job in jobs])
    for (i, leading, trailing, _), value in zip(jobs, translated):
        parts[i] = leading + value + trailing
    return "".join(parts)


def note_bounds(lines: list[str]) -> tuple[int, int] | None:
    start = next((i for i, line in enumerate(lines) if line.startswith("Notiz:")), None)
    if start is None:
        return None
    end = start + 1
    while end < len(lines):
        line = lines[end]
        if line.strip() and not line.startswith((" ", "\t")):
            break
        end += 1
    return start, end


def extract_note_markup(lines: list[str], start: int, end: int) -> str:
    first = lines[start].rstrip("\n").split(":", 1)[1].strip()
    continuation = "".join(lines[start + 1 : end])
    if first in {"|-", "|", ">-", ">", ""}:
        raw = continuation
    elif first in {"''", '""'} and not continuation.strip():
        return ""
    else:
        raw = first + ("\n" + continuation if continuation else "")
    return textwrap.dedent(raw).strip("\n")


def serialize_note(markup: str) -> list[str]:
    if not markup.strip():
        return ["Notiz: ''\n"]
    out = ["Notiz: |-\n"]
    for line in markup.splitlines():
        out.append(("  " + line if line else "") + "\n")
    return out


def process_card(path: Path, translator: CardTranslator) -> None:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)

    # Translate every non-empty definition. Source cards are restored from main,
    # where Definition is German; short entries must not depend on language hints.
    def_jobs: list[tuple[int, str]] = []
    for i, raw in enumerate(lines):
        line = raw.rstrip("\n")
        stripped = line.strip()
        if stripped.startswith("#"):
            body = stripped[1:].strip()
            if body in COMMENT_REPLACEMENTS:
                indent = line[: len(line) - len(line.lstrip())]
                newline = "\n" if raw.endswith("\n") else ""
                lines[i] = f"{indent}# {COMMENT_REPLACEMENTS[body]}{newline}"
        if line.startswith("Definition:"):
            value = line.split(":", 1)[1].strip()
            if value:
                def_jobs.append((i, value))

    if def_jobs:
        translated_defs = translator.de.translate([value for _, value in def_jobs])
        for (idx, _), value in zip(def_jobs, translated_defs):
            newline = "\n" if lines[idx].endswith("\n") else ""
            lines[idx] = f"Definition: {value}{newline}"

    # Translate English example lines directly from their preceding French lines.
    example_jobs: list[tuple[int, str, str]] = []
    in_examples = False
    pair_pos = 0
    current_fr: str | None = None
    for i, raw in enumerate(lines):
        line = raw.rstrip("\n")
        stripped = line.strip()
        if line and not line.startswith((" ", "\t")):
            in_examples = stripped.startswith("Beispielsätze:")
            pair_pos = 0
            current_fr = None
            continue
        if not in_examples or not stripped or not line.startswith((" ", "\t")):
            continue
        if pair_pos % 2 == 0:
            current_fr = stripped
        elif current_fr is not None:
            indent = line[: len(line) - len(line.lstrip())]
            example_jobs.append((i, indent, current_fr))
        pair_pos += 1

    if example_jobs:
        translated_examples = translator.translate_fr_with_emphasis([src for _, _, src in example_jobs])
        for (idx, indent, _), value in zip(example_jobs, translated_examples):
            newline = "\n" if lines[idx].endswith("\n") else ""
            lines[idx] = f"{indent}{value}{newline}"

    # Normalize the note to a YAML block scalar so translation is not discarded
    # merely because sentence length changes the number of physical lines.
    bounds = note_bounds(lines)
    if bounds:
        start, end = bounds
        markup = extract_note_markup(lines, start, end)
        if markup:
            translated_note = translate_note_markup(translator, markup)
            lines[start:end] = serialize_note(translated_note)

    path.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--paths-file", required=True)
    parser.add_argument("--batch-size", type=int, default=16)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    paths = [
        root / line.strip()
        for line in Path(args.paths_file).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    translator = CardTranslator(root=root, batch_size=args.batch_size)
    for path in paths:
        if path.suffix == ".yml" and path.parent.name == "cards":
            process_card(path, translator)


if __name__ == "__main__":
    main()
