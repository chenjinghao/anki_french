#!/usr/bin/env python3
"""Stronger 500-card gate for French-source v6 card translation."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import v6_pilot as base
import v6_scale_pilot as scale
import v6_card_pilot as pilot

MANUAL_SAMPLE_COUNT = 60

SCALE_EXPECTATIONS = {
    "cards/0121_contre.yml": [
        ("Les enfants se sont blottis *contre* leur mère.", re.compile(r"\b(?:snuggl|cuddl|huddled).*\bmother\b", re.I)),
    ],
    "cards/0217_mieux.yml": [
        ("Je ne vous ai jamais *mieux* aimée.", re.compile(r"\bnever\b.*\bloved?\b.*\bmore\b", re.I)),
    ],
    "cards/0696_porte.yml": [
        ("La *porte* de la cuisine grince terriblement.", re.compile(r"\bdoor\b.*\bcreaks?\b", re.I)),
    ],
    "cards/1128_emporter.yml": [
        ('"Je peux avoir ce sandwich à *emporter* ?"', re.compile(r"\b(?:to go|takeaway|take away)\b", re.I)),
    ],
    "cards/2123_commande.yml": [
        ("Dès ce jour nous vous passons *commande* pour cet ouvrage.", re.compile(r"\b(?:place|placing).*\border\b", re.I)),
    ],
    "cards/2267_remporter.yml": [
        ("L'autorité revenait à celui qui *remportait* la victoire.", re.compile(r"\b(?:won|winner)\b", re.I)),
    ],
    "cards/2423_protester.yml": [
        ("Marie a *protesté* de son innocence devant le juge.", re.compile(r"\b(?:asserted|protested|maintained)\b.*\binnocence\b", re.I)),
    ],
    "cards/2542_camion.yml": [
        ("Le *camion* de déménagement arrivera demain matin à huit heures.", re.compile(r"\bmoving truck\b", re.I)),
    ],
    "cards/3130_cibler.yml": [
        ("Elles pourront frapper des groupes *ciblés*.", re.compile(r"\b(?:strike|hit|attack)\b.*\btargeted\b", re.I)),
    ],
    "cards/3427_dériver.yml": [
        ("Le mot « étudiant » *dérive* du participe présent du verbe « étudier ».", re.compile(r"\b(?:derives?|derived)\b.*\bpresent participle\b.*\bétudier\b", re.I)),
    ],
    "cards/3693_abstenir.yml": [
        ("Vous feriez mieux de vous *abstenir*.", re.compile(r"\babstain\b", re.I)),
    ],
    "cards/3981_haïr.yml": [
        ("J'ai toujours *haï* la campagne.", re.compile(r"\bhated?\b.*\bcountryside\b", re.I)),
    ],
    "cards/4269_engin.yml": [
        ("Les ouvriers utilisent un *engin* de levage pour déplacer les matériaux lourds.", re.compile(r"\blifting (?:equipment|device|machine)\b", re.I)),
    ],
    "cards/4556_chocolat.yml": [
        ("Cette tablette de *chocolat* noir est délicieuse.", re.compile(r"\b(?:bar|tablet) of dark\b.*\bchocolate\b", re.I)),
    ],
    "cards/4700_triple.yml": [
        ("Le professeur a demandé une copie en *triple* exemplaire.", re.compile(r"\b(?:triplicate|three copies)\b", re.I)),
    ],
}


def strict_extra_checks(path: str, current: str, original: str, errors: list[str]) -> None:
    cur_def = base.definition(current)
    old_def = base.definition(original)
    if old_def and cur_def == old_def and re.search(r"[A-Za-zÀ-ÖØ-öø-ÿÄÖÜäöüß]", old_def):
        errors.append(f"{path}: definition unchanged from German source: {cur_def[:140]}")

    try:
        pairs = base.example_pairs(current)
    except ValueError:
        return
    pair_map = {fr: en for fr, en in pairs}
    for fr, expected in SCALE_EXPECTATIONS.get(path, []):
        en = pair_map.get(fr, "")
        if not en or not expected.search(en):
            errors.append(f"{path}: scale semantic regression for {fr[:90]} -> {en[:140]}")

    # Preserve the learner cue: a highlighted French target should normally have
    # at least one highlighted span in its English translation as well.
    for i, (fr, en) in enumerate(pairs, 1):
        if "*" in fr and "*" not in en:
            errors.append(f"{path}: emphasis lost in example {i}: {en[:140]}")


def validate(root: Path, paths: list[str], report_path: Path) -> int:
    errors: list[str] = []
    regression_samples: list[str] = []
    for rel in paths:
        current = (root / rel).read_text(encoding="utf-8")
        original = base.git_show(rel)
        pilot.validate_card(rel, current, original, errors, regression_samples)
        strict_extra_checks(rel, current, original, errors)

    manual_samples: list[str] = []
    if paths:
        count = min(MANUAL_SAMPLE_COUNT, len(paths))
        indices = sorted({round(i * (len(paths) - 1) / max(1, count - 1)) for i in range(count)})
        for idx in indices:
            rel = paths[idx]
            current = (root / rel).read_text(encoding="utf-8")
            try:
                pairs = base.example_pairs(current)
            except ValueError:
                continue
            manual_samples.append(f"## SCALE2 SAMPLE {rel}")
            manual_samples.append("Definition: " + base.definition(current))
            for fr, en in pairs[:4]:
                manual_samples.append(f"FR: {fr}\nEN: {en}")

    lines = [
        "V6 CARD SCALE PILOT QUALITY REPORT — FRENCH-SOURCE REVISION",
        f"Cards checked: {len(paths)}",
        f"Errors: {len(errors)}",
        "",
    ]
    if errors:
        lines.append("ERRORS")
        lines.extend(f"- {error}" for error in errors)
        lines.append("")
    lines.append("KNOWN REGRESSION SAMPLES")
    lines.extend(regression_samples)
    lines.append("")
    lines.append("EVENLY DISTRIBUTED MANUAL-REVIEW SAMPLES")
    lines.extend(manual_samples)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Cards checked: {len(paths)}; errors: {len(errors)}")
    print(f"Report: {report_path}")
    return 1 if errors else 0


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p_select = sub.add_parser("select")
    p_select.add_argument("--root", default=".")
    p_select.add_argument("--output", required=True)
    p_select.add_argument("--shard", type=int)
    p_select.add_argument("--shards", type=int)
    p_validate = sub.add_parser("validate")
    p_validate.add_argument("--root", default=".")
    p_validate.add_argument("--paths-file", required=True)
    p_validate.add_argument("--report", required=True)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if args.command == "select":
        paths = scale.select_scale_cards(root)
        if (args.shard is None) != (args.shards is None):
            parser.error("--shard and --shards must be supplied together")
        if args.shard is not None:
            paths = scale.shard_paths(paths, args.shard, args.shards)
        Path(args.output).write_text("\n".join(paths) + "\n", encoding="utf-8")
        print(f"Selected {len(paths)} scale2 cards")
        return

    paths = [line.strip() for line in Path(args.paths_file).read_text(encoding="utf-8").splitlines() if line.strip()]
    raise SystemExit(validate(root, paths, Path(args.report)))


if __name__ == "__main__":
    main()
