#!/usr/bin/env python3
"""Build the English French 5000 Anki package from the original shared deck.

The original .apkg is used as a donor for generated fields, note/card identities,
and media. Repository-controlled YAML fields, card templates, and grammar content
are then replaced with the English source in this repository.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import tempfile
from pathlib import Path
from urllib.parse import quote

import sass
import yaml

from anki.collection import (
    Collection,
    DeckIdLimit,
    ExportAnkiPackageOptions,
    ImportAnkiPackageOptions,
    ImportAnkiPackageRequest,
)

CONTROLLED_FIELDS = [
    "Rang",
    "Wort",
    "Wortart",
    "Wort mit Artikel",
    "Femininum / Plural",
    "IPA",
    "Definition",
    "Register",
    "Beispielsätze",
    "Notiz",
]

CATEGORY_NAMES = {
    "Orthografie": "Orthography",
    "Aussprache": "Pronunciation",
    "Artikel": "Articles",
    "Substantive": "Nouns",
    "Adjektive": "Adjectives",
    "Adverbien": "Adverbs",
    "Pronomen": "Pronouns",
    "Fragen": "Questions",
    "Verben": "Verbs",
    "Zeitformen und Modi": "Tenses and Moods",
    "Partizip": "Participles",
    "Passiv": "Passive Voice",
    "Ergänzung des Verbs": "Verb Complements",
    "Relativsätze": "Relative Clauses",
    "Bedingungssätze": "Conditional Sentences",
    "Präpositionen": "Prepositions",
    "Konjunktionen": "Conjunctions",
    "Verneinung": "Negation",
    "Inversion": "Inversion",
    "Indirekte Rede": "Indirect Speech",
    "Informelle Sprache": "Informal Language",
    "Zahlen und Zeitangaben": "Numbers and Time Expressions",
    "Vokabeln": "Vocabulary",
}

TENSES = {
    "P": ["Présent"],
    "PC": ["Passé composé"],
    "IT": ["Imparfait"],
    "F": ["Futur simple"],
    "IF": ["Impératif"],
    "G": ["Gérondif"],
    "C": ["Conditionnel"],
    "S": ["Subjonctif"],
    "SI": ["Subjonctif imparfait"],
    "PS": ["Passé simple"],
}

SECTION_TITLE_RE = re.compile(
    r'(<div\s+class="section-title"[^>]*>.*?</div>)', re.IGNORECASE | re.DOTALL
)
LEADING_NUMBER_RE = re.compile(r"^\d+\s+")
MODEL_REQUIRED = {"Rang", "Wort", "Definition", "Beispielsätze"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-apkg", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--version",
        default=os.environ.get("GITHUB_SHA", "local")[:12],
        help="Version token used in the grammar media filename.",
    )
    return parser.parse_args()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def strip_order_prefix(name: str) -> str:
    return LEADING_NUMBER_RE.sub("", name).strip()


def normalize_field_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def parse_source_card(path: Path) -> dict[str, object]:
    """Parse the repository's deliberately simple YAML-like card format.

    Translation can introduce unquoted colons into scalar values (for example
    ``Definition: of which:``), which strict YAML rejects. The card files only
    use top-level ``key: value`` entries plus indented literal blocks, so a
    purpose-built parser is safer and preserves learner text verbatim.
    """
    lines = read_text(path).splitlines()
    data: dict[str, object] = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line or line.lstrip().startswith("#"):
            i += 1
            continue
        if line[:1].isspace():
            raise RuntimeError(f"{path}:{i + 1}: unexpected indentation outside a block")
        if ":" not in line:
            raise RuntimeError(f"{path}:{i + 1}: expected top-level key: value")
        key, raw_value = line.split(":", 1)
        key = key.strip()
        value = raw_value.lstrip()

        if value in {"|", "|-", "|+", ">", ">-", ">+"}:
            block: list[str] = []
            i += 1
            while i < len(lines):
                child = lines[i]
                if child and not child[:1].isspace():
                    break
                if child.startswith("  "):
                    block.append(child[2:])
                elif child.startswith("\t"):
                    block.append(child[1:])
                elif child == "":
                    block.append("")
                else:
                    block.append(child.lstrip())
                i += 1
            text = "\n".join(block)
            if value in {"|", "|+"}:
                text += "\n"
            data[key] = text
            continue

        if " #" in value:
            value = value.split(" #", 1)[0].rstrip()

        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            try:
                parsed = yaml.safe_load(value)
                value = "" if parsed is None else str(parsed)
            except yaml.YAMLError:
                value = value[1:-1]

        data[key] = value
        i += 1

    return data


def load_cards(repo_root: Path) -> dict[int, dict[str, object]]:
    files = sorted((repo_root / "cards").glob("*.yml"))
    if len(files) != 5000:
        raise RuntimeError(f"Expected 5000 YAML cards, found {len(files)}")

    cards: dict[int, dict[str, object]] = {}
    for path in files:
        data = parse_source_card(path)
        if "Rang" not in data:
            raise RuntimeError(f"{path}: missing Rang")
        rank = int(data["Rang"])
        if rank in cards:
            raise RuntimeError(f"Duplicate Rang {rank}: {path}")
        cards[rank] = data

    expected = set(range(1, 5001))
    if set(cards) != expected:
        missing = sorted(expected - set(cards))
        extra = sorted(set(cards) - expected)
        raise RuntimeError(f"Rank set is not 1..5000; missing={missing[:10]} extra={extra[:10]}")
    return cards


def model_field_names(model: dict) -> list[str]:
    return [field["name"] for field in model["flds"]]


def choose_model(col: Collection) -> dict:
    candidates = []
    for model in col.models.all():
        fields = set(model_field_names(model))
        overlap = len(fields & MODEL_REQUIRED)
        candidates.append((overlap, int(model["id"]), model))
        print(
            "MODEL",
            model.get("name"),
            "id=",
            model.get("id"),
            "fields=",
            model_field_names(model),
            "templates=",
            [t.get("name") for t in model.get("tmpls", [])],
        )
    candidates.sort(key=lambda row: (row[0], row[1]), reverse=True)
    if not candidates or candidates[0][0] != len(MODEL_REQUIRED):
        raise RuntimeError("Could not find French 5000 notetype by required fields")
    model = candidates[0][2]
    fields = set(model_field_names(model))
    missing = [name for name in CONTROLLED_FIELDS if name not in fields]
    if missing:
        raise RuntimeError(f"Donor notetype is missing source-controlled fields: {missing}")
    return model


def patch_notes(col: Collection, model: dict, cards: dict[int, dict[str, object]]) -> None:
    model_id = int(model["id"])
    note_ids = col.db.list("select id from notes where mid = ?", model_id)
    if len(note_ids) != 5000:
        raise RuntimeError(f"Expected 5000 donor notes, found {len(note_ids)}")

    donor_by_rank: dict[int, int] = {}
    for nid in note_ids:
        note = col.get_note(nid)
        try:
            rank = int(note["Rang"])
        except Exception as exc:
            raise RuntimeError(f"Note {nid} has invalid Rang {note['Rang']!r}") from exc
        if rank in donor_by_rank:
            raise RuntimeError(f"Duplicate donor rank {rank}")
        donor_by_rank[rank] = nid

    if set(donor_by_rank) != set(cards):
        raise RuntimeError("Donor/source rank sets differ")

    changed = 0
    for rank in range(1, 5001):
        note = col.get_note(donor_by_rank[rank])
        source = cards[rank]
        for field in CONTROLLED_FIELDS:
            note[field] = normalize_field_value(source.get(field, ""))
        col.update_note(note)
        changed += 1

    print(f"UPDATED NOTES: {changed}")


def grammar_id(path: Path) -> str:
    return strip_order_prefix(path.stem)


def build_grammar_json(repo_root: Path, version: str, media_dir: Path) -> str:
    grammar_root = repo_root / "grammar"
    paths = sorted(grammar_root.rglob("*.html"))
    if len(paths) != 156:
        raise RuntimeError(f"Expected 156 grammar pages, found {len(paths)}")

    content: dict[str, str] = {}
    section_titles: dict[str, str] = {}
    github: dict[str, str] = {}
    index: dict[str, list[str]] = {}

    for path in paths:
        rel = path.relative_to(grammar_root)
        gid = grammar_id(path)
        if gid in content:
            raise RuntimeError(f"Duplicate grammar ID {gid!r}: {path}")

        raw = read_text(path)
        content[gid] = raw
        match = SECTION_TITLE_RE.search(raw)
        if match:
            section_titles[gid] = match.group(1)
        else:
            section_titles[gid] = (
                f'<div class="section-title" data-topic="">{html.escape(gid)}</div>'
            )

        quoted = quote(str(Path("grammar") / rel).replace(os.sep, "/"), safe="/")
        github[gid] = (
            "https://github.com/chenjinghao/anki_french/blob/main/" + quoted
        )

        top = rel.parts[0]
        if top == "_":
            continue
        category_key = strip_order_prefix(top)
        category = CATEGORY_NAMES.get(category_key, category_key)
        index.setdefault(category, []).append(gid)

    payload = {
        "index": index,
        "tenses": TENSES,
        "content": content,
        "github": github,
        "sectionTitles": section_titles,
    }
    filename = f"FR5000_grammar_{version}.json"
    target = media_dir / filename
    target.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"GRAMMAR JSON: pages={len(content)} file={filename} bytes={target.stat().st_size}")
    return filename


def compile_css(repo_root: Path) -> str:
    templates = repo_root / "card_templates"
    return sass.compile(
        filename=str(templates / "style.scss"),
        include_paths=[str(templates)],
        output_style="compressed",
    )


def replace_all(text: str, replacements: dict[str, str]) -> str:
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def unresolved_placeholders(text: str) -> list[str]:
    return sorted(set(re.findall(r"___[A-Z0-9_]+___", text)))


def compile_templates(repo_root: Path, version: str) -> dict[str, tuple[str, str]]:
    root = repo_root / "card_templates"
    date = dt.date.today().isoformat()
    persistence = read_text(root / "persistence.js")
    cloze = read_text(root / "cloze_game.js")
    common = read_text(root / "common.js")
    dictionary = read_text(root / "dict.js")
    back_js_raw = read_text(root / "back.js")
    back_html_raw = read_text(root / "back.html")
    front_fr_raw = read_text(root / "front_FRDE.html")
    front_en_raw = read_text(root / "front_DEFR.html")

    back_html_raw = back_html_raw.replace(
        "{{Wort mit article}}", "{{Wort mit Artikel}}"
    )
    back_html_raw = back_html_raw.replace(
        'https://ankiweb.net/shared/info/1677131827',
        'https://github.com/chenjinghao/anki_french/releases',
    )

    shared_front = cloze + "\n" + common

    front_fr = replace_all(
        front_fr_raw,
        {
            "___PERSISTENCE___": persistence,
            "___COMMONJS___": shared_front,
            "___FRONT_FRDE___": read_text(root / "front_FRDE.js"),
            "___GOOGLE_TTS_API_KEY___": "",
        },
    )
    front_en = replace_all(
        front_en_raw,
        {
            "___PERSISTENCE___": persistence,
            "___COMMONJS___": shared_front,
            "___FRONT_DEFR___": read_text(root / "front_DEFR.js"),
            "___GOOGLE_TTS_API_KEY___": "",
        },
    )

    def back(config_name: str) -> str:
        config = read_text(root / config_name)
        back_js = back_js_raw.replace("___CONFIG___", config)
        bundle = cloze + "\n" + common + "\n" + back_js + "\n" + dictionary
        return replace_all(
            back_html_raw,
            {
                "___PERSISTENCE___": persistence,
                "___BACKJS___": bundle,
                "___VERSION___": version,
                "___DATE___": date,
                "___GOOGLE_TTS_API_KEY___": "",
            },
        )

    back_fr = back("back_FRDE_config.js")
    back_en = back("back_DEFR_config.js")

    result = {
        "fr-en": (front_fr, back_fr),
        "en-fr": (front_en, back_en),
    }
    for side, pair in result.items():
        for part_name, text in zip(("front", "back"), pair):
            unresolved = unresolved_placeholders(text)
            if unresolved:
                raise RuntimeError(
                    f"{side} {part_name} has unresolved placeholders: {unresolved}"
                )
    return result


def patch_notetype(col: Collection, model: dict, repo_root: Path, version: str) -> int:
    compiled = compile_templates(repo_root, version)
    model["css"] = compile_css(repo_root)
    model["name"] = "French 5000"

    found_fr_en = 0
    found_en_fr = 0
    for tmpl in model["tmpls"]:
        qfmt = tmpl.get("qfmt", "")
        if "{{Definition}}" in qfmt:
            front, back = compiled["en-fr"]
            tmpl["name"] = "English → French"
            found_en_fr += 1
        else:
            front, back = compiled["fr-en"]
            tmpl["name"] = "French → English"
            found_fr_en += 1
        tmpl["qfmt"] = front
        tmpl["afmt"] = back

    if found_fr_en < 1 or found_en_fr < 1:
        raise RuntimeError(
            f"Could not identify both card directions: fr-en={found_fr_en}, en-fr={found_en_fr}"
        )
    col.models.save(model)
    print(
        f"PATCHED NOTETYPE: id={model['id']} templates={len(model['tmpls'])} "
        f"fr-en={found_fr_en} en-fr={found_en_fr}"
    )
    return int(model["id"])


def choose_primary_deck(col: Collection) -> tuple[int, int]:
    rows = col.db.all(
        "select did, count(*) from cards group by did order by count(*) desc"
    )
    if not rows:
        raise RuntimeError("Donor package imported no cards")
    deck_id, card_count = int(rows[0][0]), int(rows[0][1])
    deck = col.decks.get(deck_id)
    if not deck:
        raise RuntimeError(f"Could not load deck id {deck_id}")
    old_name = deck.get("name", "")
    deck["name"] = "French 5000"
    col.decks.save(deck)
    print(f"PRIMARY DECK: id={deck_id} cards={card_count} {old_name!r} -> 'French 5000'")
    return deck_id, card_count


def import_donor(col: Collection, source_apkg: Path) -> None:
    print(f"IMPORT DONOR: {source_apkg} bytes={source_apkg.stat().st_size}")
    response = col.import_anki_package(
        ImportAnkiPackageRequest(
            package_path=str(source_apkg.resolve()),
            options=ImportAnkiPackageOptions(
                merge_notetypes=True,
                with_scheduling=False,
                with_deck_configs=True,
            ),
        )
    )
    print("IMPORT RESPONSE:", response)


def export_package(col: Collection, output: Path, deck_id: int) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()
    col.export_anki_package(
        out_path=str(output.resolve()),
        options=ExportAnkiPackageOptions(
            with_scheduling=False,
            with_deck_configs=True,
            with_media=True,
            legacy=False,
        ),
        limit=DeckIdLimit(deck_id=deck_id),
    )
    if not output.exists() or output.stat().st_size < 100_000:
        raise RuntimeError("Export did not produce a plausible .apkg")
    print(f"EXPORTED: {output} bytes={output.stat().st_size}")


def validate_export(output: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="french5000-validate-") as tmp:
        col = Collection(str(Path(tmp) / "collection.anki2"))
        try:
            col.import_anki_package(
                ImportAnkiPackageRequest(
                    package_path=str(output.resolve()),
                    options=ImportAnkiPackageOptions(
                        merge_notetypes=True,
                        with_scheduling=False,
                        with_deck_configs=True,
                    ),
                )
            )
            model = choose_model(col)
            fields = set(model_field_names(model))
            if not set(CONTROLLED_FIELDS).issubset(fields):
                raise RuntimeError("Re-imported notetype lost controlled fields")

            note_ids = col.db.list("select id from notes where mid = ?", int(model["id"]))
            if len(note_ids) != 5000:
                raise RuntimeError(f"Re-import validation found {len(note_ids)} notes")
            rank_one = None
            for nid in note_ids:
                note = col.get_note(nid)
                if note["Rang"] == "1":
                    rank_one = note
                    break
            if rank_one is None:
                raise RuntimeError("Re-import validation could not find rank 1")
            if not rank_one["Definition"].strip():
                raise RuntimeError("Rank 1 definition is empty")
            if rank_one["Definition"].strip().lower() in {"der/die/das", "der, die, das"}:
                raise RuntimeError("Rank 1 definition still appears German")

            for tmpl in model["tmpls"]:
                unresolved = unresolved_placeholders(tmpl.get("qfmt", "")) + unresolved_placeholders(
                    tmpl.get("afmt", "")
                )
                if unresolved:
                    raise RuntimeError(
                        f"Re-imported template {tmpl.get('name')} has placeholders {unresolved}"
                    )
                if "{{Wort mit article}}" in tmpl.get("afmt", ""):
                    raise RuntimeError("Bad translated internal field placeholder remains")

            media_dir = Path(col.media.dir())
            grammar_files = list(media_dir.glob("FR5000_grammar_*.json"))
            if not grammar_files:
                raise RuntimeError("Grammar JSON is missing from exported media")
            grammar = json.loads(grammar_files[0].read_text(encoding="utf-8"))
            if len(grammar.get("content", {})) != 156:
                raise RuntimeError(
                    f"Grammar JSON has {len(grammar.get('content', {}))} pages, expected 156"
                )

            card_count = int(col.db.scalar("select count(*) from cards") or 0)
            media_count = sum(1 for p in media_dir.iterdir() if p.is_file())
            print(
                "VALIDATION OK:",
                f"notes={len(note_ids)} cards={card_count} media={media_count}",
                f"model={model.get('name')!r}",
                f"rank1={rank_one['Definition']!r}",
                f"grammar_pages={len(grammar['content'])}",
            )
        finally:
            col.close()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    source = args.source_apkg.resolve()
    output = args.output.resolve()
    if not source.is_file():
        raise SystemExit(f"Source .apkg not found: {source}")

    cards = load_cards(repo_root)

    with tempfile.TemporaryDirectory(prefix="french5000-build-") as tmp:
        collection_path = Path(tmp) / "collection.anki2"
        col = Collection(str(collection_path))
        try:
            import_donor(col, source)
            model = choose_model(col)
            patch_notes(col, model, cards)
            model_id = patch_notetype(col, model, repo_root, args.version)
            deck_id, donor_cards = choose_primary_deck(col)
            media_dir = Path(col.media.dir())
            grammar_file = build_grammar_json(repo_root, args.version, media_dir)
            print(
                f"BUILD READY: model={model_id} donor_cards={donor_cards} "
                f"media_dir={media_dir} grammar={grammar_file}"
            )
            export_package(col, output, deck_id)
        finally:
            col.close()

    validate_export(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
