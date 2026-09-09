#!/usr/bin/env python3
"""Finalize English-facing repository docs and reject broken translations."""
from __future__ import annotations

import html
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿŒœÇç’'-]+")
TAG_RE = re.compile(r"<[^>]+>")
TAG_SPLIT_RE = re.compile(r"(<[^>]+>)")
OPEN_TAG_RE = re.compile(r"^<\s*([A-Za-z][\w:-]*)\b")
CLOSE_TAG_RE = re.compile(r"^<\s*/\s*([A-Za-z][\w:-]*)\s*>")
CLASS_RE = re.compile(r"\bclass\s*=\s*(['\"])(.*?)\1", re.I)

IMMUTABLE_CARD_FIELDS = (
    "Rang:", "Wort:", "Wortart:", "Wort mit Artikel:", "Femininum / Plural:", "IPA:"
)

# Deliberately excludes forms that are ordinary English words (man, war, was, die,
# hat, in, am) and cross-language cognates (verb, adverb, singular, plural).
GERMAN_OUTPUT_WORDS = {
    "der", "den", "dem", "des", "das", "ein", "eine", "einen", "einem", "einer",
    "und", "oder", "aber", "nicht", "mit", "für", "von", "aus", "zu", "zur", "zum",
    "auf", "bei", "ist", "sind", "wird", "werden", "kann", "können", "muss", "müssen",
    "haben", "wenn", "dass", "auch", "nur", "sehr", "mehr", "weniger", "vor", "nach",
    "ohne", "über", "unter", "zwischen", "seit", "durch", "gegen", "wegen", "beim",
    "vom", "ins", "ich", "sie", "wir", "ihr", "wer", "wen", "wem", "wo", "wie",
    "mein", "dein", "sein", "unser", "euer", "dies", "diese", "dieser", "dieses",
    "führer", "führerin", "geschlecht", "weiblich", "männlich", "verwendung",
    "gebrauch", "bildung", "etymologisch", "paradoxerweise", "unterschiedlich",
    "keiner", "einziger", "wohnung",
}

GERMAN_SOURCE_EXACT = {
    "Verwendung", "Gebrauch", "Geschlecht", "Weiblich", "weiblich", "Männlich",
    "männlich", "Bildung", "Morgen", "Vormittag", "Nachmittag", "Abend", "Nacht",
    "Wort", "Sprache", "Zahl", "Aussprache", "Stellung", "Bedeutung", "Schreibweise",
    "Hinweis", "Achtung", "Ausnahme", "Ausnahmen", "Regel", "Regeln", "Beispiel",
    "Beispiele", "Etymologie",
}
GERMAN_SOURCE_WORDS = GERMAN_OUTPUT_WORDS | {
    "die", "hat", "waren", "war", "man", "noch", "schon", "kein", "keine", "hier",
    "zehn", "jahre", "jahr", "steht", "eigene", "seine", "präposition", "artikel",
    "substantiv", "adjektiv", "pronomen", "satz", "sätze",
}
GERMAN_SOURCE_SHAPE_RE = re.compile(
    r"\b[A-Za-zÄÖÜäöüß]+(?:keit|keiten|heit|heiten|lich|liche|lichen|licher|liches|"
    r"isch|ische|ischen|ischer|isches|erweise|schaft|schaften)\b",
    re.I,
)


def git_show(path: Path, ref: str = "origin/main") -> str:
    rel = path.relative_to(ROOT).as_posix()
    proc = subprocess.run(
        ["git", "show", f"{ref}:{rel}"],
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Could not read {rel} from {ref}: {proc.stderr.strip()}")
    return proc.stdout


def collect_french_terms() -> set[str]:
    terms = {
        "le", "la", "les", "un", "une", "des", "de", "du", "au", "aux", "à",
        "en", "y", "ce", "cet", "cette", "ces", "je", "j'", "tu", "il", "elle",
        "nous", "vous", "ils", "elles", "me", "te", "se", "lui", "leur", "que",
        "qui", "dont", "où", "ne", "pas", "plus", "et", "ou", "mais", "si", "hier",
    }
    for path in (ROOT / "cards").glob("*.yml"):
        original = git_show(path)
        for line in original.splitlines():
            if line.startswith(("Wort: ", "Wort mit Artikel: ", "Femininum / Plural: ")):
                value = line.split(":", 1)[1]
                for token in WORD_RE.findall(value):
                    terms.add(token.lower().replace("’", "'"))
    return terms


FRENCH_TERMS: set[str] | None = None


def french_terms() -> set[str]:
    global FRENCH_TERMS
    if FRENCH_TERMS is None:
        FRENCH_TERMS = collect_french_terms()
    return FRENCH_TERMS


def is_french_fragment(text: str) -> bool:
    tokens = [t.lower().replace("’", "'") for t in WORD_RE.findall(html.unescape(text))]
    return bool(tokens and len(tokens) <= 4 and all(t in french_terms() for t in tokens))


def output_german_score(text: str) -> int:
    words = [w.lower().replace("’", "'") for w in WORD_RE.findall(html.unescape(text))]
    score = sum(1 for w in words if w in GERMAN_OUTPUT_WORDS)
    if any(w in {"führer", "führerin"} for w in words):
        score += 1
    return score


def source_likely_german(text: str) -> bool:
    value = html.unescape(text).strip()
    if not value or is_french_fragment(value):
        return False
    if value in GERMAN_SOURCE_EXACT:
        return True
    words = [w.lower().replace("’", "'") for w in WORD_RE.findall(value)]
    if any(w in GERMAN_SOURCE_WORDS for w in words):
        return True
    if GERMAN_SOURCE_SHAPE_RE.search(value):
        return True
    return False


def card_definition_text(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("Definition:"):
            return line.split(":", 1)[1].strip()
    return ""


def card_definition(path: Path) -> str:
    return card_definition_text(path.read_text(encoding="utf-8"))


def example_blocks(text: str) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] = []
    in_examples = False
    for line in text.splitlines():
        if line and not line.startswith(" "):
            if in_examples and current:
                blocks.append(current)
                current = []
            in_examples = line.startswith("Beispielsätze:")
            continue
        if not in_examples:
            continue
        if not line.strip():
            if current:
                blocks.append(current)
                current = []
            continue
        current.append(line.strip())
    if in_examples and current:
        blocks.append(current)
    return blocks


def note_payload(text: str) -> str:
    lines = text.splitlines(keepends=True)
    start = None
    end = None
    for i, raw in enumerate(lines):
        line = raw.rstrip("\n")
        if line.startswith("Notiz:"):
            start = i + 1
            continue
        if start is not None and line and not line.startswith(" "):
            end = i
            break
    if start is None:
        return ""
    if end is None:
        end = len(lines)
    return "".join(lines[start:end])


def immutable_fields(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        for prefix in IMMUTABLE_CARD_FIELDS:
            if line.startswith(prefix):
                out[prefix] = line
                break
    return out


def _class_stack_nodes(html_text: str, *, protected: bool) -> list[str]:
    nodes: list[str] = []
    protect_stack: list[bool] = []
    for part in TAG_SPLIT_RE.split(html_text):
        if not part:
            continue
        if part.startswith("<"):
            if part.startswith("<!--") or part.startswith("<!") or part.startswith("<?"):
                continue
            if CLOSE_TAG_RE.match(part):
                if protect_stack:
                    protect_stack.pop()
                continue
            m = OPEN_TAG_RE.match(part)
            if m and not part.rstrip().endswith("/>"):
                classes = ""
                cm = CLASS_RE.search(part)
                if cm:
                    classes = cm.group(2)
                own_protected = any(c in {"fr", "ipa"} for c in classes.split()) or m.group(1).lower() == "code"
                protect_stack.append((protect_stack[-1] if protect_stack else False) or own_protected)
            continue

        in_protected = bool(protect_stack and protect_stack[-1])
        if in_protected != protected:
            continue
        value = re.sub(r"\s+", " ", part).strip()
        if value:
            nodes.append(value)
    return nodes


def visible_non_french_nodes(html_text: str) -> list[str]:
    return _class_stack_nodes(html_text, protected=False)


def protected_french_nodes(html_text: str) -> list[str]:
    return _class_stack_nodes(html_text, protected=True)


def unchanged_german_nodes(current: str, original: str) -> list[str]:
    current_nodes = visible_non_french_nodes(current)
    original_nodes = visible_non_french_nodes(original)
    if len(current_nodes) != len(original_nodes):
        return []
    bad: list[str] = []
    for new, old in zip(current_nodes, original_nodes):
        if new != old:
            continue
        stripped = html.unescape(old).strip()
        if len(WORD_RE.findall(stripped)) <= 1 and len(re.sub(r"\W", "", stripped)) <= 3:
            continue
        if source_likely_german(old):
            bad.append(old)
    return bad


def suspicious_output_nodes(text: str) -> list[str]:
    return [node for node in visible_non_french_nodes(text) if output_german_score(node) >= 2]


def finalize_templates() -> None:
    common = ROOT / "card_templates" / "common.js"
    if common.exists():
        text = common.read_text(encoding="utf-8")
        text = text.replace('if (lang === "de-DE") {', 'if (lang === "en-US") {')
        text = text.replace('languageCode: "de-DE"', 'languageCode: "en-US"')
        text = text.replace('"de-DE-Chirp3-HD-"', '"en-US-Chirp3-HD-"')
        text = text.replace('// replace with German quote marks »...«', '// replace with English quote marks “...”')
        text = text.replace(
            'text = text.replaceAll(/"(?![^<]*>)(.+?)"(?![^<]*>)/g, "»\\u2060$1\\u2060«");',
            'text = text.replaceAll(/"(?![^<]*>)(.+?)"(?![^<]*>)/g, "“\\u2060$1\\u2060”");',
        )
        common.write_text(text, encoding="utf-8")


def validate_cards() -> list[str]:
    errors: list[str] = []
    for path in sorted((ROOT / "cards").glob("*.yml")):
        current = path.read_text(encoding="utf-8")
        original = git_show(path)

        if "ZXQ" in current:
            errors.append(f"{path}: corrupted placeholder token")
            continue
        if immutable_fields(current) != immutable_fields(original):
            errors.append(f"{path}: compatibility-sensitive card fields changed")

        current_blocks = example_blocks(current)
        original_blocks = example_blocks(original)
        if len(current_blocks) != len(original_blocks):
            errors.append(f"{path}: example block count changed ({len(original_blocks)} -> {len(current_blocks)})")
            continue

        for block_no, (new_block, old_block) in enumerate(zip(current_blocks, original_blocks), 1):
            if len(new_block) != 2:
                errors.append(f"{path}: example block {block_no} has {len(new_block)} lines instead of 2")
                continue
            if len(old_block) != 2:
                errors.append(f"{path}: original example block {block_no} is unexpectedly malformed")
                continue
            if new_block[0] != old_block[0]:
                errors.append(f"{path}: French text changed in example block {block_no}")

            translated = new_block[1]
            original_de = old_block[1]
            if translated == original_de and source_likely_german(original_de):
                errors.append(f"{path}: untranslated example block {block_no}: {translated[:120]}")
            elif output_german_score(translated) >= 2:
                errors.append(f"{path}: likely German remains in example block {block_no}: {translated[:120]}")
            if translated.count("*") % 2:
                errors.append(f"{path}: unmatched emphasis marker in example block {block_no}")
            if "**" in translated:
                errors.append(f"{path}: doubled emphasis marker in example block {block_no}")

        definition = card_definition_text(current)
        original_definition = card_definition_text(original)
        if definition == original_definition and source_likely_german(original_definition):
            errors.append(f"{path}: definition was not translated: {definition}")
        elif output_german_score(definition) >= 2:
            errors.append(f"{path}: likely German remains in definition: {definition}")

        current_note = note_payload(current)
        original_note = note_payload(original)
        if current_note and original_note:
            if TAG_RE.findall(current_note) != TAG_RE.findall(original_note):
                errors.append(f"{path}: note HTML tags/attributes changed")
            if protected_french_nodes(current_note) != protected_french_nodes(original_note):
                errors.append(f"{path}: French/IPA note content changed")
            unchanged = unchanged_german_nodes(current_note, original_note)
            if unchanged:
                errors.append(f"{path}: untranslated note text remains: {unchanged[0][:120]}")
            suspicious = suspicious_output_nodes(current_note)
            if suspicious:
                errors.append(f"{path}: likely German remains in note: {suspicious[0][:120]}")

        if len(errors) >= 80:
            break
    return errors


def validate_grammar() -> list[str]:
    errors: list[str] = []
    for path in sorted((ROOT / "grammar").rglob("*.html")):
        current = path.read_text(encoding="utf-8")
        original = git_show(path)
        if "ZXQ" in current:
            errors.append(f"{path}: corrupted placeholder token")
            continue
        if TAG_RE.findall(current) != TAG_RE.findall(original):
            errors.append(f"{path}: HTML tags/attributes changed during translation")
            continue
        if protected_french_nodes(current) != protected_french_nodes(original):
            errors.append(f"{path}: French/IPA grammar content changed during translation")
            continue

        unchanged = unchanged_german_nodes(current, original)
        if unchanged:
            errors.append(f"{path}: untranslated grammar text remains: {unchanged[0][:140]}")
            continue
        suspicious = suspicious_output_nodes(current)
        if suspicious:
            errors.append(f"{path}: likely German remains: {suspicious[0][:140]}")

        if len(errors) >= 40:
            break
    return errors


def validate_templates() -> list[str]:
    errors: list[str] = []
    for path in sorted((ROOT / "card_templates").glob("*")):
        if not path.is_file() or path.suffix not in {".html", ".js", ".scss"}:
            continue
        text = path.read_text(encoding="utf-8")
        if "ZXQ" in text:
            errors.append(f"{path}: corrupted placeholder token")
        if '"de-DE"' in text:
            errors.append(f"{path}: German TTS locale remains")
        if "autoPlaySentenceInGerman" in text:
            errors.append(f"{path}: German-facing autoplay option remains")
    return errors


def validate_translation() -> None:
    errors = validate_cards() + validate_grammar() + validate_templates()
    if errors:
        raise SystemExit("Translation quality gate failed:\n" + "\n".join(errors[:160]))


def sync_words() -> None:
    path = ROOT / "WORDS.md"
    lines = path.read_text(encoding="utf-8").splitlines()
    card_by_rank = {}
    for card in sorted((ROOT / "cards").glob("*.yml")):
        rank = int(card.name.split("_", 1)[0])
        card_by_rank[rank] = card_definition(card)

    out = []
    for i, line in enumerate(lines):
        if i == 0:
            out.append("| Rank | Word | Definition | Example Sentences | Note | Link |")
            continue
        m = re.match(r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*(.*?)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*\[.*?\]\((.*?)\)\s*\|$", line)
        if not m:
            out.append(line)
            continue
        rank = int(m.group(1))
        word = m.group(2).strip()
        examples = m.group(4).strip()
        note = m.group(5).strip()
        link = m.group(6).strip()
        definition = card_by_rank.get(rank, m.group(3).strip())
        out.append(f"| {rank} | {word} | {definition} | {examples} | {note} | [Edit]({link}) |")
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def write_readme() -> None:
    text = """# French 5000

Help improve **French 5000**, an Anki deck for English speakers learning French. The deck contains the 5,000 most frequent French words, with extensive example sentences, grammar notes, audio, and more.

This repository is the English-learning version of the original German-to-French deck. French source text is preserved; German learner-facing definitions, translations, grammar explanations, and interface text are translated into English.

## Contributing

The [cards](cards) directory contains all 5,000 cards in YAML format.

1. Fork this repository.
2. Edit card files in `cards`.
3. Commit your changes.
4. Open a pull request.

## Grammar

The [grammar](grammar) directory contains the grammar-library entries. The directory hierarchy is also used to organize the grammar library.

A grammar entry can be embedded in a card note with `<grammar data-id="ID"></grammar>`. Some internal IDs and schema field names remain in German for compatibility with the original Anki note type; learner-facing text is English.

## License

The deck itself is released under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). Source code in [card_templates](card_templates) is licensed under Apache 2.0.

## Overview

The repository contains **5,000 cards** with **149,711 example sentences** (29.9 per card on average). **2,568 cards** include an additional note.

See the [complete word list](WORDS.md).
"""
    (ROOT / "README.md").write_text(text, encoding="utf-8")


if __name__ == "__main__":
    finalize_templates()
    validate_translation()
    sync_words()
    write_readme()
