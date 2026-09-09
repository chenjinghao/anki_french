#!/usr/bin/env python3
"""Translate learner-facing German in the anki_french sources to English.

This script is designed for CI sharding. It preserves French source text and the
repository's internal German identifiers (field names, CSS classes and grammar IDs)
so existing Anki templates and grammar links remain compatible.
"""
from __future__ import annotations

import argparse
import html
import os
import re
from pathlib import Path
from typing import Iterable, List

import torch
from transformers import MarianMTModel, MarianTokenizer

MODEL_NAME = os.environ.get("TRANSLATION_MODEL", "Helsinki-NLP/opus-mt-de-en")

COMMENT_REPLACEMENTS = {
    "Diese Felder bitte nicht ändern.": "Please do not change these fields.",
    "Diese Felder gerne verbessern!": "Feel free to improve these fields!",
    "Beispiel: ↘Sachtext ↗Mündlich": "Example: ↘formal/written ↗spoken",
    "Beispielsätze müssen durch Zeilenumbrüche getrennt werden.": "Example sentences must be separated by line breaks.",
    "Zwischen jedem Paar kommen zwei Zeilenumbrüche.": "Separate each pair with two line breaks.",
    "Notizen können HTML enthalten. Um Beispielsätze zu formatieren, gerne dieses Format benutzen:": "Notes may contain HTML. To format example sentences, you can use this structure:",
}

TEMPLATE_REPLACEMENTS = {
    "Hilfsverb": "auxiliary verb",
    "intransitives Verb": "intransitive verb",
    "transitives Verb": "transitive verb",
    "reflexives Verb": "reflexive verb",
    "Adjektiv": "adjective",
    "Adverb": "adverb",
    "Artikel": "article",
    "Apposition": "apposition",
    "Konjunktion": "conjunction",
    "Determinativ": "determiner",
    "Interjektion": "interjection",
    "Numeral": "numeral",
    "Präposition": "preposition",
    "Pronomen": "pronoun",
    "Substantiv": "noun",
    "unpersönliches": "impersonal",
    "nur in Plural": "plural only",
    "feminines": "feminine",
    "maskulines": "masculine",
    "unveränderliches": "invariable",
    "Nur unregelmäßige anzeigen": "Show irregular forms only",
    "Alles anzeigen": "Show all",
    "Es ist ein Fehler beim Laden der Grammatik-Bibliothek aufgetreten:": "An error occurred while loading the grammar library:",
    "Bitte melde das Problem auf": "Please report the problem on",
    "Fehler: Grammatik ${id} nicht gefunden.": "Error: grammar entry ${id} not found.",
    "Auf GitHub bearbeiten": "Edit on GitHub",
    "Grammatik durchsuchen...": "Search grammar...",
    "Keine Ergebnisse gefunden.": "No results found.",
    "Grammatik-Bibliothek": "Grammar Library",
    "Grammatik": "Grammar",
    "Spenden": "Donate",
    "Stand:": "Version:",
    "Das Deck wurde zuletzt vor ": "The deck was last updated ",
    " Tagen aktualisiert. Führe ein ": " days ago. Install an ",
    "Update</a> durch, um die neuesten Verbesserungen zu erhalten. Der Lernfortschritt bleibt erhalten.": "update</a> to get the latest improvements. Your learning progress will be preserved.",
}

GERMAN_HINTS = re.compile(
    r"\b(?:der|die|das|den|dem|des|ein|eine|einer|einem|einen|und|oder|aber|nicht|mit|für|von|aus|zu|im|in|auf|bei|ist|sind|wird|werden|kann|können|muss|müssen|hat|haben|als|wenn|dass|dies|diese|dieser|dieses|auch|nur|sehr|mehr|weniger|vor|nach|ohne|über|unter|zwischen|seit|durch|gegen|wegen|beim|zum|zur|vom|ins|am|man|ich|du|er|sie|wir|ihr)\b|[äöüß]",
    re.IGNORECASE,
)

TAG_RE = re.compile(r"<[^>]+>")
ENTITY_RE = re.compile(r"&(?:[A-Za-z][A-Za-z0-9]+|#\d+|#x[0-9A-Fa-f]+);")


class Translator:
    def __init__(self, batch_size: int = 48):
        self.batch_size = batch_size
        self.tokenizer = MarianTokenizer.from_pretrained(MODEL_NAME)
        self.model = MarianMTModel.from_pretrained(MODEL_NAME)
        self.model.eval()
        torch.set_num_threads(max(1, min(2, os.cpu_count() or 1)))

    def translate(self, texts: List[str]) -> List[str]:
        if not texts:
            return []
        out: List[str] = []
        for start in range(0, len(texts), self.batch_size):
            batch = texts[start : start + self.batch_size]
            encoded = self.tokenizer(batch, return_tensors="pt", padding=True, truncation=True, max_length=384)
            with torch.inference_mode():
                generated = self.model.generate(**encoded, max_new_tokens=384, num_beams=1)
            out.extend(self.tokenizer.batch_decode(generated, skip_special_tokens=True))
        return out


def looks_german(text: str) -> bool:
    text = html.unescape(text).strip()
    return bool(text and len(text) >= 2 and GERMAN_HINTS.search(text))


def protect_markup(text: str):
    mapping = {}
    counter = 0

    def protect(pattern: re.Pattern, kind: str, s: str) -> str:
        nonlocal counter
        def repl(match):
            nonlocal counter
            token = f"ZXQ{kind}{counter:04d}QXZ"
            counter += 1
            mapping[token] = match.group(0)
            return token
        return pattern.sub(repl, s)

    protected = protect(TAG_RE, "TAG", text)
    protected = protect(ENTITY_RE, "ENT", protected)
    chars = []
    for ch in protected:
        if ch == "*":
            token = f"ZXQMD{counter:04d}QXZ"
            counter += 1
            mapping[token] = "*"
            chars.append(token)
        else:
            chars.append(ch)
    return "".join(chars), mapping


def restore_markup(text: str, mapping: dict[str, str]) -> str:
    for token, original in mapping.items():
        text = text.replace(token, original)
    return text


def translate_markup_aware(translator: Translator, texts: List[str]) -> List[str]:
    protected_texts, mappings, indices = [], [], []
    results = list(texts)
    for i, text in enumerate(texts):
        if not looks_german(TAG_RE.sub(" ", text)):
            continue
        protected, mapping = protect_markup(text)
        protected_texts.append(protected)
        mappings.append(mapping)
        indices.append(i)
    translated = translator.translate(protected_texts)
    for i, value, mapping in zip(indices, translated, mappings):
        results[i] = restore_markup(value, mapping)
    return results


def process_card(path: Path, translator: Translator) -> None:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    jobs = []
    in_examples = False
    in_note = False
    example_block_line = 0

    for i, raw in enumerate(lines):
        newline = "\n" if raw.endswith("\n") else ""
        line = raw[:-1] if newline else raw
        stripped = line.strip()

        if not line.startswith(" "):
            in_examples = stripped.startswith("Beispielsätze:")
            in_note = stripped.startswith("Notiz:")
            example_block_line = 0

        if stripped.startswith("#"):
            body = stripped[1:].strip()
            if body in COMMENT_REPLACEMENTS:
                indent = line[: len(line) - len(line.lstrip())]
                lines[i] = f"{indent}# {COMMENT_REPLACEMENTS[body]}{newline}"
            elif looks_german(body):
                prefix = line[: line.index("#") + 1] + " "
                jobs.append((i, prefix, body))
            continue

        if line.startswith("Definition:"):
            value = line.split(":", 1)[1].strip()
            if value:
                jobs.append((i, "Definition: ", value))
            continue

        if line.startswith("Register:"):
            value = line.split(":", 1)[1].strip()
            if value and value not in {"''", '""'} and looks_german(value):
                jobs.append((i, "Register: ", value))
            continue

        if in_examples and line.startswith("  "):
            if not stripped:
                example_block_line = 0
                continue
            if example_block_line % 2 == 1:
                indent = line[: len(line) - len(line.lstrip())]
                jobs.append((i, indent, line.strip()))
            example_block_line += 1
            continue

        if in_note and line.startswith("  ") and stripped:
            if re.fullmatch(r"<grammar\b[^>]*></grammar>", stripped):
                continue
            visible = TAG_RE.sub(" ", stripped)
            if looks_german(visible):
                indent = line[: len(line) - len(line.lstrip())]
                jobs.append((i, indent, line.strip()))

    if jobs:
        translated = translate_markup_aware(translator, [j[2] for j in jobs])
        for (line_index, prefix, _), value in zip(jobs, translated):
            newline = "\n" if lines[line_index].endswith("\n") else ""
            lines[line_index] = f"{prefix}{value}{newline}"

    path.write_text("".join(lines), encoding="utf-8")


def process_grammar_html(path: Path, translator: Translator) -> None:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    jobs = []
    for i, raw in enumerate(lines):
        newline = "\n" if raw.endswith("\n") else ""
        line = raw[:-1] if newline else raw
        stripped = line.strip()
        if not stripped:
            continue
        if 'class="fr' in stripped or "class='fr" in stripped or 'class="ipa' in stripped:
            continue
        visible = TAG_RE.sub(" ", stripped)
        if looks_german(visible):
            indent = line[: len(line) - len(line.lstrip())]
            jobs.append((i, indent, stripped))
    translated = translate_markup_aware(translator, [j[2] for j in jobs])
    for (line_index, indent, _), value in zip(jobs, translated):
        newline = "\n" if lines[line_index].endswith("\n") else ""
        lines[line_index] = f"{indent}{value}{newline}"
    path.write_text("".join(lines), encoding="utf-8")


def process_template_file(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    for old, new in TEMPLATE_REPLACEMENTS.items():
        text = text.replace(old, new)
    text = text.replace('lang: "de-DE"', 'lang: "en-US"')
    text = text.replace('autoPlaySentenceInGerman', 'autoPlaySentenceInEnglish')
    text = text.replace('.localeCompare(b.replace("*", ""), "de",', '.localeCompare(b.replace("*", ""), "en",')
    path.write_text(text, encoding="utf-8")


def select_shard(paths: Iterable[Path], shard: int, shards: int) -> List[Path]:
    ordered = sorted(paths, key=lambda p: p.as_posix())
    return [p for i, p in enumerate(ordered) if i % shards == shard]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--shard", type=int, required=True)
    parser.add_argument("--shards", type=int, required=True)
    parser.add_argument("--batch-size", type=int, default=48)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    translator = Translator(batch_size=args.batch_size)
    for path in select_shard((root / "cards").glob("*.yml"), args.shard, args.shards):
        process_card(path, translator)
    for path in select_shard((root / "grammar").rglob("*.html"), args.shard, args.shards):
        process_grammar_html(path, translator)

    if args.shard == 0:
        listing = root / "ankiweb_listing.html"
        if listing.exists():
            process_grammar_html(listing, translator)
        for path in (root / "card_templates").glob("*"):
            if path.is_file() and path.suffix in {".html", ".js", ".scss"}:
                process_template_file(path)


if __name__ == "__main__":
    main()
