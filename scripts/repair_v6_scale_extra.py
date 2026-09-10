#!/usr/bin/env python3
"""Second-pass reviewed repairs for the French-source 500-card v6 pilot.

These repairs are source-keyed: the preserved French sentence determines the
reviewed English replacement. They cover failures found only after expanding
manual review from the original regression set to the 500-card sample.
"""
from __future__ import annotations

import argparse
from pathlib import Path

EXAMPLES = {
    "Vive *la* politique, vive *l'*amour.": "Long live politics, long live love.",
    "Nous ne *suivons* pas cet article en magasin.": "We don't *stock* this item in the store.",
    "La fenêtre donne *du côté de* la mer.": "The window *faces the sea*.",
    "Le chat est devenu *propre* en très peu de temps.": "The cat became *house-trained* very quickly.",
    "Ils ont mené une affaire *propre* sans aucun scandale.": "They conducted a *clean operation* without any scandal.",
    "Elle a *perdu* l'habitude de fumer depuis trois mois.": "She has been *out of the habit of smoking* for three months.",
    "Ce *million* d'euros servira à rénover l'école.": "This *one million euros* will be used to renovate the school.",
    "Le gardien a *placé* une sentinelle devant la porte.": "The guard *posted* a sentry at the door.",
    "Elle n'arrive jamais à *placer* un mot pendant les réunions familiales.": "She never manages to *get a word in* during family meetings.",
    "L'auteur a *placé* l'intrigue dans les années 1920.": "The author *set* the plot in the 1920s.",
    "Marie a toujours eu des *facilités* en mathématiques.": "Marie has always been *talented* at mathematics.",
    "Le système *fédéral* allemand accorde beaucoup d'autonomie aux Länder.": "Germany's *federal* system gives its states a great deal of autonomy.",
    "Je pourrai en *témoigner*, au besoin, dit-elle.": "I can *testify* to that if necessary, she said.",
    '"Si tu refuses son invitation, *automatiquement*, elle ne t\'invitera plus."': '"If you turn down her invitation, *naturally*, she won\'t invite you again."',
    "Ils inventent les *regroupements* de populations.": "They devise ways of *grouping* populations.",
}

DEFINITIONS = {
    "cards/0012_ce.yml": "this; that; it",
    "cards/0193_pourquoi.yml": "why",
    "cards/0402_unique.yml": "only; unique",
    "cards/0445_européen.yml": "European; European person",
    "cards/1296_britannique.yml": "British; Briton",
    "cards/1320_joindre.yml": "to join; connect; reach someone",
    "cards/1859_strict.yml": "strict; rigorous",
    "cards/1890_foutre.yml": "to fuck; do; put [vulgar/informal]",
    "cards/1895_chrétien.yml": "Christian",
    "cards/2650_chimique.yml": "chemical",
    "cards/3106_décrocher.yml": "to take down; get; land",
    "cards/3597_ménager.yml": "to spare; household; domestic",
    "cards/3741_masculin.yml": "masculine; male",
    "cards/4185_réciproque.yml": "reciprocal; counterpart",
    "cards/4784_acceptation.yml": "acceptance; approval",
}


def replace_definition(text: str, value: str) -> str:
    lines = text.splitlines(keepends=True)
    start = next((i for i, line in enumerate(lines) if line.startswith("Definition:")), None)
    if start is None:
        return text
    end = start + 1
    while end < len(lines):
        line = lines[end]
        if line.strip() and not line.startswith((" ", "\t")):
            break
        end += 1
    return "".join(lines[:start] + [f"Definition: {value}\n"] + lines[end:])


def repair_card(path: Path, rel: str) -> None:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
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
        elif current_fr in EXAMPLES:
            indent = line[: len(line) - len(line.lstrip())]
            newline = "\n" if raw.endswith("\n") else ""
            lines[i] = f"{indent}{EXAMPLES[current_fr]}{newline}"
        pair_pos += 1
    text = "".join(lines)
    if rel in DEFINITIONS:
        text = replace_definition(text, DEFINITIONS[rel])
    path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--paths-file", required=True)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    for rel in Path(args.paths_file).read_text(encoding="utf-8").splitlines():
        rel = rel.strip()
        if rel:
            repair_card(root / rel, rel)


if __name__ == "__main__":
    main()
