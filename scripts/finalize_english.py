#!/usr/bin/env python3
"""Finalize English-facing repository docs and reject broken translations."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GERMAN_WORDS = {
    "ich", "du", "wir", "ihr", "sie", "er", "nicht", "und", "oder", "aber",
    "ist", "sind", "war", "waren", "wird", "werden", "hat", "haben", "kann",
    "können", "muss", "müssen", "der", "die", "das", "den", "dem", "des",
    "ein", "eine", "einen", "einem", "einer", "mit", "für", "von", "aus",
    "zu", "zur", "zum", "auf", "bei", "wenn", "dass", "auch", "nur", "sehr",
    "wie", "was", "wer", "wen", "wem", "wo", "hier", "dort", "mein", "dein",
    "sein", "unser", "euer", "dies", "diese", "dieser", "dieses", "man", "noch",
    "schon", "kein", "keine", "ohne", "über", "unter", "zwischen", "seit", "durch",
}
WORD_RE = re.compile(r"[A-Za-zÄÖÜäöüß]+")
TAG_RE = re.compile(r"<[^>]+>")
TAG_SPLIT_RE = re.compile(r"(<[^>]+>)")
OPEN_TAG_RE = re.compile(r"^<\s*([A-Za-z][\w:-]*)\b")
CLOSE_TAG_RE = re.compile(r"^<\s*/\s*([A-Za-z][\w:-]*)\s*>")
CLASS_RE = re.compile(r"\bclass\s*=\s*(['\"])(.*?)\1", re.I)
IMMUTABLE_CARD_FIELDS = (
    "Rang:", "Wort:", "Wortart:", "Wort mit Artikel:", "Femininum / Plural:", "IPA:"
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


def card_definition_text(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("Definition:"):
            return line.split(":", 1)[1].strip()
    return ""


def card_definition(path: Path) -> str:
    return card_definition_text(path.read_text(encoding="utf-8"))


def german_score(text: str) -> int:
    words = [w.lower() for w in WORD_RE.findall(text)]
    score = sum(1 for w in words if w in GERMAN_WORDS)
    if re.search(r"[äöüß]", text, re.I):
        score += 2
    return score


def example_blocks(text: str) -> list[list[str]]:
    """Return non-empty line blocks under Beispielsätze; each block must be [FR, translation]."""
    blocks: list[list[str]] = []
    current: list[str] = []
    in_examples = False
    for line in text.splitlines():
        if not line.startswith(" "):
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


def immutable_fields(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        for prefix in IMMUTABLE_CARD_FIELDS:
            if line.startswith(prefix):
                out[prefix] = line
                break
    return out


def visible_non_french_nodes(html_text: str) -> list[str]:
    """Extract visible text outside .fr/.ipa nodes, preserving a tiny HTML stack."""
    nodes: list[str] = []
    skip_stack: list[bool] = []
    for part in TAG_SPLIT_RE.split(html_text):
        if not part:
            continue
        if part.startswith("<"):
            if part.startswith("<!--") or part.startswith("<!") or part.startswith("<?"):
                continue
            if CLOSE_TAG_RE.match(part):
                if skip_stack:
                    skip_stack.pop()
                continue
            m = OPEN_TAG_RE.match(part)
            if m and not part.rstrip().endswith("/>"):
                classes = ""
                cm = CLASS_RE.search(part)
                if cm:
                    classes = cm.group(2)
                own_skip = any(c in {"fr", "ipa"} for c in classes.split())
                skip_stack.append((skip_stack[-1] if skip_stack else False) or own_skip)
            continue
        if skip_stack and skip_stack[-1]:
            continue
        value = re.sub(r"\s+", " ", part).strip()
        if value:
            nodes.append(value)
    return nodes


def validate_cards() -> list[str]:
    errors: list[str] = []
    for path in sorted((ROOT / "cards").glob("*.yml")):
        current = path.read_text(encoding="utf-8")
        original = git_show(path)

        if "ZXQ" in current:
            errors.append(f"{path}: corrupted placeholder token")
            continue

        # French-side invariants: immutable fields and every French example line must remain exact.
        if immutable_fields(current) != immutable_fields(original):
            errors.append(f"{path}: compatibility-sensitive card fields changed")

        current_blocks = example_blocks(current)
        original_blocks = example_blocks(original)
        if len(current_blocks) != len(original_blocks):
            errors.append(
                f"{path}: example block count changed ({len(original_blocks)} -> {len(current_blocks)})"
            )
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
            if german_score(new_block[1]) >= 2:
                errors.append(
                    f"{path}: likely German remains in example block {block_no}: {new_block[1][:120]}"
                )

        definition = card_definition_text(current)
        if german_score(definition) >= 2:
            errors.append(f"{path}: likely German remains in definition: {definition}")

        if len(errors) >= 50:
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

        # Tags and all attributes (including grammar IDs and French classes) must stay exact.
        if TAG_RE.findall(current) != TAG_RE.findall(original):
            errors.append(f"{path}: HTML tags/attributes changed during translation")
            continue

        suspicious = [n for n in visible_non_french_nodes(current) if german_score(n) >= 2]
        if suspicious:
            errors.append(f"{path}: likely German remains: {suspicious[0][:140]}")

        if len(errors) >= 25:
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
        if 'lang: "de-DE"' in text:
            errors.append(f"{path}: German TTS locale remains")
        if "autoPlaySentenceInGerman" in text:
            errors.append(f"{path}: German-facing autoplay option remains")
    return errors


def validate_translation() -> None:
    errors = validate_cards() + validate_grammar() + validate_templates()
    if errors:
        raise SystemExit("Translation quality gate failed:\n" + "\n".join(errors[:100]))


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
    validate_translation()
    sync_words()
    write_readme()
