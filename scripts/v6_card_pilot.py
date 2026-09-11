#!/usr/bin/env python3
"""Card-only selection and QA for the v6 NLLB pilot.

This isolates the 5,000-card translation problem from grammar HTML, whose prose
needs a separate conversion strategy. The pilot intentionally includes known
historical failure cases and fails on both structural and semantic regressions.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import v6_pilot as base
import v6_pilot_v2 as qa

CARD_RANKS = set(range(1, 31)) | {
    34, 44, 50, 100, 120, 123, 135, 167, 195, 208, 237, 242, 244, 250,
    265, 307, 316, 402, 425, 500, 504, 535, 685, 750, 1000, 1042, 1250,
    1440, 1500, 1705, 1750, 1890, 2000, 2044, 2250, 2500, 2516, 2750,
    3000, 3029, 3250, 3427, 3460, 3500, 3624, 3750, 4000, 4250, 4440,
    4500, 4750, 5000,
}

BAD_CARD_ENGLISH = re.compile(
    r"\b(?:linguistic attire|has always been a mathematician|lost with man and mouse|"
    r"milliönes|hotel zur post|stands? \*?on the street|she missed him by ear|"
    r"how to see yourself again|getting used to smoking|thousands upon thousands|"
    r"found him dead, drowned|window goes to the sea|article in business|"
    r"guard set up a guard|left corner of the gate)\b|ZXQ",
    re.I,
)

SEMANTIC_EXPECTATIONS = {
    "cards/0021_par.yml": [
        ("Ils ont réussi *par* tous les moyens.", re.compile(r"\bthey\b.*\bsucceed(?:ed)?\b", re.I)),
    ],
    "cards/0022_je.yml": [
        ("Où suis-*je* ? *Je* ne reconnais pas cet endroit.", re.compile(r"\bwhere am i\b.*\b(?:recognize|recognise)\b", re.I)),
    ],
    "cards/0120_suivre.yml": [
        ("Nous ne *suivons* pas cet article en magasin.", re.compile(r"\b(?:stock|carry)\b.*\b(?:item|product)\b", re.I)),
    ],
    "cards/0123_côté.yml": [
        ("La fenêtre donne *du côté de* la mer.", re.compile(r"\b(?:faces?|overlooks?)\b.*\bsea\b", re.I)),
    ],
    "cards/0195_trop.yml": [
        ("Vous insistez *trop* sur les détails et négligez l'essentiel.", re.compile(r"\byou\b.*\btoo much\b.*\bdetails\b", re.I)),
    ],
    "cards/0237_propre.yml": [
        ("Le chat est devenu *propre* en très peu de temps.", re.compile(r"\b(?:house[- ]trained|toilet[- ]trained)\b", re.I)),
        ("Ils ont mené une affaire *propre* sans aucun scandale.", re.compile(r"\bclean\b.*\b(?:operation|business|affair)\b", re.I)),
    ],
    "cards/0244_retrouver.yml": [
        ("Tu as *retrouvé* mes clés ? Je les cherche partout !", re.compile(r"\bkeys\b.*\b(?:looking|searching)\b|\b(?:looking|searching)\b.*\bkeys\b", re.I)),
        ('"*Comme on se retrouve* !"', re.compile(r"\b(?:fancy meeting|meet again|see you again)\b", re.I)),
    ],
    "cards/0250_perdre.yml": [
        ("Elle a *perdu* l'habitude de fumer depuis trois mois.", re.compile(r"\b(?:out of the habit|no longer)\b.*\bsmok", re.I)),
    ],
    "cards/0265_ensuite.yml": [
        ("*Ensuite* de quoi, ils se sont réconciliés.", re.compile(r"\bafter (?:that|which)\b.*\breconcil", re.I)),
    ],
    "cards/0307_million.yml": [
        ("Nous avons reçu des *millions et des millions* de demandes.", re.compile(r"\bmillions and millions\b", re.I)),
        ("Ce *million* d'euros servira à rénover l'école.", re.compile(r"\bmillion euros\b.*\brenovat", re.I)),
    ],
    "cards/0504_oublier.yml": [
        ("J'ai *oublié* comment on fait une tarte.", re.compile(r"\b(?:make|bake)\b.*\btart\b", re.I)),
    ],
    "cards/0535_placer.yml": [
        ("Le gardien a *placé* une sentinelle devant la porte.", re.compile(r"\bposted\b.*\bsentry\b", re.I)),
        ("Elle n'arrive jamais à *placer* un mot pendant les réunions familiales.", re.compile(r"\bget a word in\b", re.I)),
        ("Le joueur a parfaitement *placé* son tir dans le coin gauche du but.", re.compile(r"\bleft corner\b.*\bgoal\b", re.I)),
        ("L'auteur a *placé* l'intrigue dans les années 1920.", re.compile(r"\bset\b.*\b(?:story|plot)\b.*\b1920", re.I)),
    ],
    "cards/1890_foutre.yml": [
        ("Elle lui a *foutu* une claque en pleine figure.", re.compile(r"\b(?:slap|slapped|smack|smacked|hit)\b.*\b(?:face|across)\b", re.I)),
    ],
    "cards/3624_facilité.yml": [
        ("Marie a toujours eu des *facilités* en mathématiques.", re.compile(r"\b(?:talent|talented|gifted)\b.*\bmath", re.I)),
        ("Sa *facilité* d'expression impressionne tout le monde.", re.compile(r"\b(?:fluency|ease)\b", re.I)),
        ("Le magasin propose des *facilités* de paiement intéressantes.", re.compile(r"\bpayment (?:options|terms|plans|facilities)\b", re.I)),
    ],
    "cards/5000_écrouler.yml": [
        ("On le trouva mort, *écroulé* dans les w.c.", re.compile(r"\b(?:slumped|collapsed)\b.*\b(?:bathroom|toilet|restroom)\b", re.I)),
        ("Le gouvernement s'est *écroulé* après un vote de défiance.", re.compile(r"\bgovernment\b.*\bcollapsed\b.*\bno confidence\b", re.I)),
    ],
}


def select_cards(root: Path) -> list[str]:
    by_rank: dict[int, Path] = {}
    for path in sorted((root / "cards").glob("*.yml")):
        try:
            rank = int(path.name.split("_", 1)[0])
        except ValueError:
            continue
        by_rank[rank] = path
    return sorted(
        by_rank[r].relative_to(root).as_posix()
        for r in CARD_RANKS
        if r in by_rank
    )


def validate_card(path: str, current: str, original: str, errors: list[str], samples: list[str]) -> None:
    before = len(errors)
    qa.validate_card(path, current, original, errors, samples)

    try:
        pairs = base.example_pairs(current)
    except ValueError:
        return
    for i, (_, en) in enumerate(pairs, 1):
        if BAD_CARD_ENGLISH.search(en):
            errors.append(f"{path}: known card mistranslation in example {i}: {en[:160]}")

    pair_map = {fr: en for fr, en in pairs}
    for fr, expected in SEMANTIC_EXPECTATIONS.get(path, []):
        en = pair_map.get(fr, "")
        if not en or not expected.search(en):
            msg = f"{path}: card semantic regression for {fr[:90]} -> {en[:140]}"
            if msg not in errors:
                errors.append(msg)

    # Surface every historically troublesome card in the report, even when it passes.
    rank = int(Path(path).name.split("_", 1)[0])
    if rank in {21, 120, 123, 135, 167, 195, 208, 237, 244, 250, 265, 307, 316, 402, 504, 535, 1890, 2516, 3624, 5000}:
        samples.append(f"## REGRESSION SAMPLE {path}")
        for fr, en in pairs[:10]:
            samples.append(f"FR: {fr}\nEN: {en}")
        note = base.note_text(current)
        if note and rank in {242, 425, 1890, 2516, 5000}:
            samples.append("NOTE: " + " ".join(base.visible_nodes(note))[:1600])
        if len(errors) > before:
            samples.append("STATUS: failed one or more checks")


def validate(root: Path, paths: list[str], report_path: Path) -> int:
    errors: list[str] = []
    samples: list[str] = []
    for rel in paths:
        current = (root / rel).read_text(encoding="utf-8")
        original = base.git_show(rel)
        validate_card(rel, current, original, errors, samples)

    lines = [
        "V6 CARD PILOT QUALITY REPORT — REVISION 4",
        f"Cards checked: {len(paths)}",
        f"Errors: {len(errors)}",
        "",
    ]
    if errors:
        lines.append("ERRORS")
        lines.extend(f"- {e}" for e in errors)
        lines.append("")
    lines.append("REGRESSION SAMPLES")
    lines.extend(samples)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(report_path.read_text(encoding="utf-8"))
    return 1 if errors else 0


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p_select = sub.add_parser("select")
    p_select.add_argument("--root", default=".")
    p_select.add_argument("--output", required=True)
    p_validate = sub.add_parser("validate")
    p_validate.add_argument("--root", default=".")
    p_validate.add_argument("--paths-file", required=True)
    p_validate.add_argument("--report", required=True)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if args.command == "select":
        paths = select_cards(root)
        Path(args.output).write_text("\n".join(paths) + "\n", encoding="utf-8")
        print(f"Selected {len(paths)} card regression files")
        return

    paths = [
        line.strip()
        for line in Path(args.paths_file).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    raise SystemExit(validate(root, paths, Path(args.report)))


if __name__ == "__main__":
    main()
