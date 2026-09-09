#!/usr/bin/env python3
"""NLLB German→English translator for the v6 quality pilot.

This is intentionally separate from the production v5 translator. It preserves
French learner text and compatibility-sensitive HTML while using a terminology
glossary before and after NLLB translation.
"""
from __future__ import annotations

import argparse
import html
import os
import re
from pathlib import Path
from typing import List

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

MODEL_NAME = os.environ.get("TRANSLATION_MODEL", "facebook/nllb-200-distilled-600M")
SRC_LANG = "deu_Latn"
TGT_LANG = "eng_Latn"

COMMENT_REPLACEMENTS = {
    "Diese Felder bitte nicht ändern.": "Please do not change these fields.",
    "Diese Felder gerne verbessern!": "Feel free to improve these fields!",
    "Beispielsätze müssen durch Zeilenumbrüche getrennt werden.": "Example sentences must be separated by line breaks.",
    "Zwischen jedem Paar kommen zwei Zeilenumbrüche.": "Separate each pair with two line breaks.",
    "Notizen können HTML enthalten. Um Beispielsätze zu formatieren, gerne dieses Format benutzen:": "Notes may contain HTML. To format example sentences, you can use this structure:",
}

# Longest/specific phrases first. These substitutions are deliberately limited to
# French-learning terminology where literal model choices have repeatedly been bad.
SOURCE_GLOSSARY = [
    (r"\bDer bestimmte Artikel\b", "The definite article"),
    (r"\bder bestimmte Artikel\b", "the definite article"),
    (r"\bdie bestimmten Artikel\b", "the definite articles"),
    (r"\bden bestimmten Artikeln\b", "the definite articles"),
    (r"\bden bestimmten Artikel\b", "the definite article"),
    (r"\bbestimmten Artikeln\b", "definite articles"),
    (r"\bbestimmten Artikel\b", "definite article"),
    (r"\bbestimmter Artikel\b", "definite article"),
    (r"\bunbestimmter Artikel\b", "indefinite article"),
    (r"\bunbestimmten Artikel\b", "indefinite article"),
    (r"\bTeilungsartikel\b", "partitive article"),
    (r"\bstumm(?:es|en|e|er) h\b", "silent h"),
    (r"\bGeschlecht(?:s)?\b", "grammatical gender"),
    (r"\bZahl des Substantivs\b", "number of the noun"),
    (r"\bSubstantive\b", "nouns"),
    (r"\bSubstantivs\b", "noun"),
    (r"\bSubstantiv\b", "noun"),
    (r"\bAdjektive\b", "adjectives"),
    (r"\bAdjektiv\b", "adjective"),
    (r"\bAdverbien\b", "adverbs"),
    (r"\bAdverb\b", "adverb"),
    (r"\bPronomen\b", "pronoun"),
    (r"\bPräpositionen\b", "prepositions"),
    (r"\bPräposition\b", "preposition"),
    (r"\bKonjunktionen\b", "conjunctions"),
    (r"\bKonjunktion\b", "conjunction"),
    (r"\bHilfsverben\b", "auxiliary verbs"),
    (r"\bHilfsverb\b", "auxiliary verb"),
    (r"\bInfinitiv\b", "infinitive"),
    (r"\bIndikativ\b", "indicative"),
    (r"\bImperativ\b", "imperative"),
    (r"\bPartizip\b", "participle"),
    (r"\bRelativsatz\b", "relative clause"),
    (r"\bRelativsätze\b", "relative clauses"),
    (r"\bNebensatz\b", "subordinate clause"),
    (r"\bNebensätze\b", "subordinate clauses"),
    (r"\bHauptsatz\b", "main clause"),
    (r"\bVokal\b", "vowel"),
    (r"\bVokalen\b", "vowels"),
    (r"\bPlural\b", "plural"),
    (r"\bSingular\b", "singular"),
]

POST_GLOSSARY = [
    (r"\b(?:specific|particular|certain) article\b", "definite article"),
    (r"\b(?:specific|particular|certain) articles\b", "definite articles"),
    (r"\bsex and number of the noun\b", "gender and number of the noun"),
    (r"\bgrammatical sex\b", "grammatical gender"),
    (r"\bArticles of division\b", "partitive articles"),
    (r"\bArticle of division\b", "partitive article"),
]

EXACT_NODE_REPLACEMENTS = {
    "bzw.": "or",
    "bzw": "or",
    "z. B.": "e.g.",
    "z.B.": "e.g.",
    "d. h.": "i.e.",
    "d.h.": "i.e.",
    "Verwendung": "Usage",
    "Gebrauch": "Usage",
    "Geschlecht": "Gender",
    "Weiblich": "Feminine",
    "weiblich": "feminine",
    "Männlich": "Masculine",
    "männlich": "masculine",
    "Bildung": "Formation",
    "Wort": "word",
    "Sprache": "language",
    "Zahl": "number",
    "Aussprache": "Pronunciation",
    "Stellung": "Position",
    "Bedeutung": "Meaning",
    "Schreibweise": "Spelling",
    "Hinweis": "Note",
    "Achtung": "Caution",
    "Ausnahme": "Exception",
    "Ausnahmen": "Exceptions",
    "Regel": "Rule",
    "Regeln": "Rules",
    "Form": "Form",
    "Formen": "Forms",
    "Beispiel": "Example",
    "Beispiele": "Examples",
    "Etymologie": "Etymology",
}

GERMAN_HINTS = re.compile(
    r"\b(?:der|die|das|den|dem|ein|eine|einer|einem|einen|und|oder|aber|nicht|"
    r"mit|für|von|aus|zu|zur|zum|auf|bei|ist|sind|wird|werden|kann|können|"
    r"muss|müssen|hat|haben|als|wenn|dass|dies|diese|dieser|dieses|auch|nur|"
    r"sehr|mehr|weniger|vor|nach|ohne|über|unter|zwischen|seit|durch|gegen|"
    r"wegen|beim|vom|ins|ich|sie|wir|ihr|wer|wen|wem|wo|wie|mein|dein|sein|"
    r"unser|euer|präposition|artikel|substantiv|adjektiv|pronomen|satz|sätze|"
    r"gebrauch|verwendung|beispiel|beispiele|geschlecht|weiblich|männlich|"
    r"bildung|steht|keiner|kein|zehn|jahre|wort|sprache|zahl)\b|[äöüß]",
    re.IGNORECASE,
)
GERMAN_SUFFIX_RE = re.compile(
    r"\b[A-Za-zÄÖÜäöüß]+(?:keit|keiten|heit|heiten|lich|liche|lichen|licher|liches|"
    r"isch|ische|ischen|ischer|isches|erweise|schaft|schaften|ung|ungen)\b",
    re.IGNORECASE,
)
TAG_SPLIT_RE = re.compile(r"(<[^>]+>)")
OPEN_TAG_RE = re.compile(r"^<\s*([A-Za-z][\w:-]*)\b")
CLOSE_TAG_RE = re.compile(r"^<\s*/\s*([A-Za-z][\w:-]*)\s*>")
CLASS_RE = re.compile(r"\bclass\s*=\s*(['\"])(.*?)\1", re.I)
EMPH_RE = re.compile(r"\*([^*]+)\*")
TOKEN_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿŒœÇç’'-]+")


def apply_source_glossary(text: str) -> str:
    for pattern, replacement in SOURCE_GLOSSARY:
        text = re.sub(pattern, replacement, text, flags=re.I)
    return text


def apply_post_glossary(text: str) -> str:
    for pattern, replacement in POST_GLOSSARY:
        text = re.sub(pattern, replacement, text, flags=re.I)
    return text


def collect_french_terms(root: Path) -> set[str]:
    terms = {
        "le", "la", "les", "un", "une", "des", "de", "du", "au", "aux", "à",
        "en", "y", "ce", "cet", "cette", "ces", "je", "j'", "tu", "il", "elle",
        "nous", "vous", "ils", "elles", "me", "te", "se", "lui", "leur", "que",
        "qui", "dont", "où", "ne", "pas", "plus", "et", "ou", "mais", "si", "hier",
        "être", "avoir", "faire", "aller", "venir", "subjonctif", "indicatif",
    }
    for path in (root / "cards").glob("*.yml"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith(("Wort: ", "Wort mit Artikel: ", "Femininum / Plural: ")):
                value = line.split(":", 1)[1]
                for token in TOKEN_RE.findall(value):
                    terms.add(token.lower().replace("’", "'"))
    return terms


class Translator:
    def __init__(self, root: Path, batch_size: int = 16):
        self.batch_size = batch_size
        self.french_terms = collect_french_terms(root)
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, src_lang=SRC_LANG)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
        self.model.eval()
        self.target_id = self.tokenizer.convert_tokens_to_ids(TGT_LANG)
        torch.set_num_threads(max(1, min(2, os.cpu_count() or 1)))

    def translate(self, texts: List[str]) -> List[str]:
        if not texts:
            return []
        out: List[str] = []
        prepared = [apply_source_glossary(t) for t in texts]
        for start in range(0, len(prepared), self.batch_size):
            batch = prepared[start : start + self.batch_size]
            encoded = self.tokenizer(
                batch, return_tensors="pt", padding=True, truncation=True, max_length=512
            )
            with torch.inference_mode():
                generated = self.model.generate(
                    **encoded,
                    forced_bos_token_id=self.target_id,
                    max_new_tokens=384,
                    num_beams=4,
                    no_repeat_ngram_size=4,
                    repetition_penalty=1.08,
                )
            decoded = self.tokenizer.batch_decode(generated, skip_special_tokens=True)
            for value in decoded:
                out.append(apply_post_glossary(value.strip()))
        return out


def looks_german(text: str) -> bool:
    value = html.unescape(text).strip()
    return bool(value and len(value) >= 2 and (GERMAN_HINTS.search(value) or GERMAN_SUFFIX_RE.search(value)))


def find_and_mark(text: str, phrase: str) -> str:
    phrase = phrase.strip().strip('"“”„.,;:!?()[]*')
    if not phrase:
        return text
    pattern = re.compile(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", re.I)
    match = pattern.search(text)
    if not match:
        return text
    return text[:match.start()] + "*" + text[match.start():match.end()] + "*" + text[match.end():]


def translate_sentences(translator: Translator, texts: List[str]) -> List[str]:
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
        value = re.sub(r"\*{2,}", "*", value)
        out.append(value)
    return out


def is_french_fragment(text: str, french_terms: set[str]) -> bool:
    tokens = [t.lower().replace("’", "'") for t in TOKEN_RE.findall(html.unescape(text))]
    return bool(tokens and len(tokens) <= 5 and all(t in french_terms for t in tokens))


def translate_html_text(translator: Translator, text: str) -> str:
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
            match = OPEN_TAG_RE.match(part)
            if match and not part.rstrip().endswith("/>"):
                tag = match.group(1).lower()
                classes = ""
                class_match = CLASS_RE.search(part)
                if class_match:
                    classes = class_match.group(2)
                protected = any(c in {"fr", "ipa"} for c in classes.split()) or tag == "code"
                stack.append((tag, (stack[-1][1] if stack else False) or protected))
            continue

        if stack and stack[-1][1]:
            continue
        stripped = html.unescape(part).strip()
        if not stripped:
            continue
        if stripped in EXACT_NODE_REPLACEMENTS:
            leading = part[:len(part) - len(part.lstrip())]
            trailing = part[len(part.rstrip()):]
            parts[i] = leading + EXACT_NODE_REPLACEMENTS[stripped] + trailing
            continue
        if is_french_fragment(stripped, translator.french_terms):
            continue
        if looks_german(part):
            leading = part[:len(part) - len(part.lstrip())]
            trailing = part[len(part.rstrip()):]
            jobs.append((i, leading, trailing, part.strip()))

    translated = translator.translate([job[3] for job in jobs])
    for (i, leading, trailing, _), value in zip(jobs, translated):
        parts[i] = leading + value + trailing
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
        stripped = line.strip()
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
                indent = line[:len(line) - len(line.lstrip())]
                lines[i] = f"{indent}# {COMMENT_REPLACEMENTS[body]}{newline}"
            continue
        if line.startswith("Definition:"):
            value = line.split(":", 1)[1].strip()
            if value and looks_german(value):
                plain_jobs.append((i, "Definition: ", value))
            continue
        if line.startswith("Register:"):
            continue
        if in_examples:
            if not stripped:
                example_block_line = 0
                continue
            if line.startswith("  "):
                if example_block_line % 2 == 1:
                    indent = line[:len(line) - len(line.lstrip())]
                    sentence_jobs.append((i, indent, line.strip()))
                example_block_line += 1

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


def process_html(path: Path, translator: Translator) -> None:
    path.write_text(translate_html_text(translator, path.read_text(encoding="utf-8")), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--paths-file", required=True)
    parser.add_argument("--batch-size", type=int, default=16)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    paths = [root / line.strip() for line in Path(args.paths_file).read_text(encoding="utf-8").splitlines() if line.strip()]
    translator = Translator(root=root, batch_size=args.batch_size)
    for path in paths:
        if path.suffix == ".yml" and path.parent.name == "cards":
            process_card(path, translator)
        elif path.suffix == ".html" and "grammar" in path.parts:
            process_html(path, translator)


if __name__ == "__main__":
    main()
