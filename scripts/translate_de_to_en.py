#!/usr/bin/env python3
"""Translate learner-facing German in the anki_french sources to English.

The translator preserves French source text plus compatibility-sensitive German
field/CSS/grammar identifiers. Card examples are translated as complete sentences;
HTML is translated by visible text node while tags/attributes and French fragments
remain untouched.
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

POST_REPLACEMENTS = {
    "[local]": "[place]",
    "[locally]": "[place]",
    "[temporal]": "[time]",
    "[temporarily]": "[time]",
    "[Articles of division]": "[partitive article]",
    "[Article of division]": "[partitive article]",
    "Articles of division": "partitive article",
    "Article of division": "partitive article",
    "==References==": "or",
}

EXACT_NODE_REPLACEMENTS = {
    "bzw.": "or",
    "bzw": "or",
    "z. B.": "e.g.",
    "z.B.": "e.g.",
    "d. h.": "i.e.",
    "d.h.": "i.e.",
}

GERMAN_HINTS = re.compile(
    r"\b(?:der|die|das|den|dem|des|ein|eine|einer|einem|einen|und|oder|aber|nicht|mit|für|von|aus|zu|im|in|auf|bei|ist|sind|wird|werden|kann|können|muss|müssen|hat|haben|als|wenn|dass|dies|diese|dieser|dieses|auch|nur|sehr|mehr|weniger|vor|nach|ohne|über|unter|zwischen|seit|durch|gegen|wegen|beim|zum|zur|vom|ins|am|man|ich|du|er|sie|wir|ihr|wer|wen|wem|wo|wie|was|mein|dein|sein|unser|euer|bzw|präposition|artikel|substantiv|adjektiv|adverb|pronomen|verb|satz|sätze|gebrauch|beispiel|beispiele)\b|[äöüß]",
    re.IGNORECASE,
)

TAG_SPLIT_RE = re.compile(r"(<[^>]+>)")
OPEN_TAG_RE = re.compile(r"^<\s*([A-Za-z][\w:-]*)\b")
CLOSE_TAG_RE = re.compile(r"^<\s*/\s*([A-Za-z][\w:-]*)\s*>")
CLASS_RE = re.compile(r"\bclass\s*=\s*(['\"])(.*?)\1", re.I)
EMPH_RE = re.compile(r"\*([^*]+)\*")
TOKEN_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿŒœÇç’'-]+")


def collect_french_terms(root: Path) -> set[str]:
    terms = {
        "le", "la", "les", "un", "une", "des", "de", "du", "au", "aux", "à",
        "en", "y", "ce", "cet", "cette", "ces", "je", "j'", "tu", "il", "elle",
        "nous", "vous", "ils", "elles", "me", "te", "se", "lui", "leur", "que",
        "qui", "dont", "où", "ne", "pas", "plus", "et", "ou", "mais", "si",
    }
    for path in (root / "cards").glob("*.yml"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith(("Wort: ", "Wort mit Artikel: ", "Femininum / Plural: ")):
                value = line.split(":", 1)[1]
                for token in TOKEN_RE.findall(value):
                    terms.add(token.lower().replace("’", "'"))
    return terms


class Translator:
    def __init__(self, root: Path, batch_size: int = 48):
        self.batch_size = batch_size
        self.french_terms = collect_french_terms(root)
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
            encoded = self.tokenizer(
                batch, return_tensors="pt", padding=True, truncation=True, max_length=384
            )
            with torch.inference_mode():
                generated = self.model.generate(**encoded, max_new_tokens=384, num_beams=2)
            decoded = self.tokenizer.batch_decode(generated, skip_special_tokens=True)
            for value in decoded:
                for old, new in POST_REPLACEMENTS.items():
                    value = value.replace(old, new)
                out.append(value)
        return out


def looks_german(text: str) -> bool:
    text = html.unescape(text).strip()
    return bool(text and len(text) >= 2 and GERMAN_HINTS.search(text))


def find_and_mark(text: str, phrase: str) -> str:
    phrase = phrase.strip().strip('"“”„.,;:!?()[]')
    if not phrase:
        return text
    pattern = re.compile(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", re.I)
    m = pattern.search(text) or re.search(re.escape(phrase), text, re.I)
    if not m:
        return text
    return text[: m.start()] + "*" + text[m.start() : m.end()] + "*" + text[m.end() :]


def translate_sentences(translator: Translator, texts: List[str]) -> List[str]:
    """Translate complete German sentences, then restore translated emphasis when matchable."""
    clean = [EMPH_RE.sub(lambda m: m.group(1), text) for text in texts]
    translated_full = translator.translate(clean)
    span_lists = [EMPH_RE.findall(text) for text in texts]
    flat_spans = [span for spans in span_lists for span in spans]
    translated_spans = translator.translate(flat_spans)
    cursor = 0
    out: List[str] = []
    for full, spans in zip(translated_full, span_lists):
        value = full
        for _ in spans:
            value = find_and_mark(value, translated_spans[cursor])
            cursor += 1
        out.append(value)
    return out


def is_french_fragment(text: str, french_terms: set[str]) -> bool:
    tokens = [t.lower().replace("’", "'") for t in TOKEN_RE.findall(html.unescape(text))]
    return bool(tokens and len(tokens) <= 4 and all(t in french_terms for t in tokens))


def translate_html_text(translator: Translator, text: str) -> str:
    """Translate visible German text nodes with HTML parsing state preserved across lines."""
    parts = TAG_SPLIT_RE.split(text)
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
            m = OPEN_TAG_RE.match(part)
            if m and not part.rstrip().endswith("/>"):
                tag = m.group(1).lower()
                classes = ""
                cm = CLASS_RE.search(part)
                if cm:
                    classes = cm.group(2)
                own_protected = any(c in {"fr", "ipa"} for c in classes.split()) or tag == "code"
                stack.append((tag, (stack[-1][1] if stack else False) or own_protected))
            continue

        if stack and stack[-1][1]:
            continue
        stripped = html.unescape(part).strip()
        if not stripped:
            continue

        parent_tag = stack[-1][0] if stack else ""
        if parent_tag in {"b", "strong", "u", "em"} and is_french_fragment(stripped, translator.french_terms):
            continue

        if stripped in EXACT_NODE_REPLACEMENTS:
            leading = part[: len(part) - len(part.lstrip())]
            trailing = part[len(part.rstrip()) :]
            parts[i] = leading + EXACT_NODE_REPLACEMENTS[stripped] + trailing
            continue

        if looks_german(part):
            leading = part[: len(part) - len(part.lstrip())]
            trailing = part[len(part.rstrip()) :]
            jobs.append((i, leading, trailing, part.strip()))

    translated = translator.translate([job[3] for job in jobs])
    for (i, leading, trailing, _), value in zip(jobs, translated):
        parts[i] = leading + value.strip() + trailing
    return "".join(parts)


def process_card(path: Path, translator: Translator) -> None:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    sentence_jobs: List[tuple[int, str, str]] = []
    plain_jobs: List[tuple[int, str, str]] = []
    in_examples = False
    in_note = False
    example_block_line = 0
    note_start: int | None = None
    note_end: int | None = None

    for i, raw in enumerate(lines):
        newline = "\n" if raw.endswith("\n") else ""
        line = raw[:-1] if newline else raw
        line = line.replace("# Beispiel: ↘Sachtext ↗Mündlich", "# Example: ↘formal/written ↗spoken")
        stripped = line.strip()
        lines[i] = line + newline

        # Blank lines inside block scalars are not top-level YAML fields.
        if line and not line.startswith(" "):
            if in_note and not stripped.startswith("Notiz:") and note_end is None:
                note_end = i
            in_examples = stripped.startswith("Beispielsätze:")
            in_note = stripped.startswith("Notiz:")
            if in_note:
                note_start = i + 1
            example_block_line = 0

        if stripped.startswith("#"):
            body = stripped[1:].strip()
            if body in COMMENT_REPLACEMENTS:
                indent = line[: len(line) - len(line.lstrip())]
                lines[i] = f"{indent}# {COMMENT_REPLACEMENTS[body]}{newline}"
            continue

        if line.startswith("Definition:"):
            value = line.split(":", 1)[1].strip()
            if value:
                plain_jobs.append((i, "Definition: ", value))
            continue

        if line.startswith("Register:"):
            value = line.split(":", 1)[1].strip()
            if value and not value.startswith(("''", '""')) and looks_german(value):
                plain_jobs.append((i, "Register: ", value))
            continue

        if in_examples:
            if not stripped:
                example_block_line = 0
                continue
            if line.startswith("  "):
                if example_block_line % 2 == 1:
                    indent = line[: len(line) - len(line.lstrip())]
                    sentence_jobs.append((i, indent, line.strip()))
                example_block_line += 1
                continue

    if in_note and note_start is not None and note_end is None:
        note_end = len(lines)

    if plain_jobs:
        translated = translator.translate([j[2] for j in plain_jobs])
        for (line_index, prefix, _), value in zip(plain_jobs, translated):
            newline = "\n" if lines[line_index].endswith("\n") else ""
            lines[line_index] = f"{prefix}{value}{newline}"

    if sentence_jobs:
        translated = translate_sentences(translator, [j[2] for j in sentence_jobs])
        for (line_index, prefix, _), value in zip(sentence_jobs, translated):
            newline = "\n" if lines[line_index].endswith("\n") else ""
            lines[line_index] = f"{prefix}{value}{newline}"

    if note_start is not None and note_end is not None and note_start < note_end:
        note_text = "".join(lines[note_start:note_end])
        translated_note = translate_html_text(translator, note_text)
        replacement = translated_note.splitlines(keepends=True)
        if len(replacement) == note_end - note_start:
            lines[note_start:note_end] = replacement

    path.write_text("".join(lines), encoding="utf-8")


def process_html_file(path: Path, translator: Translator) -> None:
    text = path.read_text(encoding="utf-8")
    path.write_text(translate_html_text(translator, text), encoding="utf-8")


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
    translator = Translator(root=root, batch_size=args.batch_size)
    for path in select_shard((root / "cards").glob("*.yml"), args.shard, args.shards):
        process_card(path, translator)
    for path in select_shard((root / "grammar").rglob("*.html"), args.shard, args.shards):
        process_html_file(path, translator)

    if args.shard == 0:
        listing = root / "ankiweb_listing.html"
        if listing.exists():
            process_html_file(listing, translator)
        for path in (root / "card_templates").glob("*"):
            if path.is_file() and path.suffix in {".html", ".js", ".scss"}:
                process_template_file(path)


if __name__ == "__main__":
    main()
