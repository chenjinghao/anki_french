#!/usr/bin/env python3
"""Second-stage QA for the NLLB v6 pilot.

Uses a strict output-German detector so ordinary English words such as young and hat
do not trigger false positives, while known German residues and semantic regressions
still fail the pilot.
"""
from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

import v6_pilot as base
from translate_de_to_en_v6 import looks_german as looks_german_source

BAD_ENGLISH = re.compile(
    r"\b(?:linguistic attire|specific article|specific articles|particular article|"
    r"particular articles|certain article|certain articles|sex and number of the noun|"
    r"has always been a mathematician|is addressed in French to the)\b|ZXQ",
    re.I,
)

OUTPUT_STRONG = re.compile(
    r"\b(?:führer|führerin|substantivs?|geschlecht|verwendet|verwendung|bedeutet|"
    r"bedeutung|hilfsverb(?:s|en)?|hauptverb(?:s|en)?|nebensatz|hauptsatz|"
    r"präposition(?:en)?|adjektiv(?:e|en)?|pronomen|konjunktion(?:en)?|"
    r"ausnahme(?:n)?|beispiel(?:e)?|bildung|weiblich|männlich|"
    r"vulgäres|umgangssprachliches|verschiedene|allgemeinen|ausdrückt|"
    r"gleichgültigkeit|zusammenhängen|schimpfwörtern|französischen)\b|[äöüß]",
    re.I,
)
OUTPUT_FUNCTION = re.compile(
    r"\b(?:der|die|das|den|dem|ein|eine|einen|einer|einem|und|oder|aber|nicht|"
    r"mit|für|von|aus|zu|zur|zum|auf|bei|ist|sind|wird|werden|kann|können|"
    r"muss|müssen|als|wenn|dass|dies|diese|dieser|dieses|auch|nur|vor|nach|"
    r"ohne|über|unter|zwischen|seit|durch|gegen|wegen|beim|vom|ins|ich|sie|"
    r"wir|ihr|wer|wen|wem|wo|wie|mein|dein|sein|unser|euer)\b",
    re.I,
)
OUTPUT_SUFFIX = re.compile(
    r"\b[A-Za-zÄÖÜäöüß]+(?:keit|heiten?|lichkeiten?|erweise|schaften?)\b",
    re.I,
)

SEMANTIC_EXPECTATIONS = {
    "cards/0022_je.yml": [
        ("Où suis-*je* ? *Je* ne reconnais pas cet endroit.", re.compile(r"\bwhere am i\b", re.I)),
    ],
    "cards/3624_facilité.yml": [
        ("Marie a toujours eu des *facilités* en mathématiques.", re.compile(r"\b(?:talent|talented|gifted)\b.*\bmath", re.I)),
        ("Sa *facilité* d'expression impressionne tout le monde.", re.compile(r"\b(?:fluency|ease)\b", re.I)),
    ],
}


def looks_german_output(text: str) -> bool:
    value = html.unescape(text).strip()
    if not value:
        return False
    if OUTPUT_STRONG.search(value) or OUTPUT_SUFFIX.search(value):
        return True
    return len(OUTPUT_FUNCTION.findall(value)) >= 2


def validate_card(path: str, current: str, original: str, errors: list[str], samples: list[str]) -> None:
    try:
        cur_pairs = base.example_pairs(current)
        old_pairs = base.example_pairs(original)
    except ValueError as exc:
        errors.append(f"{path}: {exc}")
        return
    if len(cur_pairs) != len(old_pairs):
        errors.append(f"{path}: example pair count changed {len(old_pairs)} -> {len(cur_pairs)}")
        return

    for i, ((cur_fr, cur_en), (old_fr, old_de)) in enumerate(zip(cur_pairs, old_pairs), 1):
        if cur_fr != old_fr:
            errors.append(f"{path}: French example {i} changed")
        if cur_en == old_de:
            errors.append(f"{path}: example {i} unchanged from German")
        if looks_german_output(cur_en):
            errors.append(f"{path}: German remains in example {i}: {cur_en[:140]}")
        if BAD_ENGLISH.search(cur_en):
            errors.append(f"{path}: known bad English in example {i}: {cur_en[:140]}")
        if base.repeated_phrase(cur_en):
            errors.append(f"{path}: repetitive example {i}: {cur_en[:140]}")

    cur_def = base.definition(current)
    old_def = base.definition(original)
    if old_def and looks_german_source(old_def) and cur_def == old_def:
        errors.append(f"{path}: German definition unchanged")
    if cur_def and (looks_german_output(cur_def) or BAD_ENGLISH.search(cur_def)):
        errors.append(f"{path}: suspicious definition: {cur_def[:140]}")

    note = base.note_text(current)
    if note:
        for node in base.visible_nodes(note):
            if looks_german_output(node):
                errors.append(f"{path}: German remains in note: {node[:160]}")
            if BAD_ENGLISH.search(node) or base.repeated_phrase(node):
                errors.append(f"{path}: suspicious note English: {node[:160]}")

    pair_map = {fr: en for fr, en in cur_pairs}
    for fr, expected in SEMANTIC_EXPECTATIONS.get(path, []):
        en = pair_map.get(fr, "")
        if not en or not expected.search(en):
            errors.append(f"{path}: semantic regression for {fr[:80]} -> {en[:120]}")

    if path.startswith(("cards/0002_", "cards/0022_", "cards/1890_", "cards/3624_")):
        samples.append(f"## {path}")
        for fr, en in cur_pairs[:8]:
            samples.append(f"FR: {fr}\nEN: {en}")
        if note:
            samples.append("NOTE: " + " ".join(base.visible_nodes(note))[:1200])


def validate_grammar(path: str, current: str, original: str, errors: list[str], samples: list[str]) -> None:
    if base.TAG_RE.findall(current) != base.TAG_RE.findall(original):
        errors.append(f"{path}: HTML tag/attribute sequence changed")
    for cls in ("fr", "ipa"):
        if base.protected_fragments(current, cls) != base.protected_fragments(original, cls):
            errors.append(f"{path}: .{cls} content changed")
    for node in base.visible_nodes(current):
        if looks_german_output(node):
            errors.append(f"{path}: German remains: {node[:160]}")
        if BAD_ENGLISH.search(node):
            errors.append(f"{path}: known bad English: {node[:160]}")
        if base.repeated_phrase(node):
            errors.append(f"{path}: repetitive English: {node[:160]}")
    if path in base.KNOWN_GRAMMAR:
        samples.append(f"## {path}")
        for node in base.visible_nodes(current)[:28]:
            samples.append(node[:600])


def validate(root: Path, paths: list[str], report_path: Path) -> int:
    errors: list[str] = []
    samples: list[str] = []
    for rel in paths:
        current = (root / rel).read_text(encoding="utf-8")
        original = base.git_show(rel)
        if rel.startswith("cards/"):
            validate_card(rel, current, original, errors, samples)
        elif rel.startswith("grammar/"):
            validate_grammar(rel, current, original, errors, samples)

    lines = [
        "V6 PILOT QUALITY REPORT — REVISION 2",
        f"Files checked: {len(paths)}",
        f"Errors: {len(errors)}",
        "",
    ]
    if errors:
        lines.append("ERRORS")
        lines.extend(f"- {e}" for e in errors)
        lines.append("")
    lines.append("REPRESENTATIVE SAMPLES")
    lines.extend(samples)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(report_path.read_text(encoding="utf-8"))
    return 1 if errors else 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--paths-file", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    paths = [
        line.strip()
        for line in Path(args.paths_file).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    raise SystemExit(validate(root, paths, Path(args.report)))


if __name__ == "__main__":
    main()
