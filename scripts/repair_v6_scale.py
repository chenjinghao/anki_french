#!/usr/bin/env python3
"""Source-aware deterministic repairs for v6 scale validation.

Repairs are keyed by the preserved French learner sentence, not by a particular
bad model output, so known semantic failures stay fixed across model revisions.
"""
from __future__ import annotations

import argparse
from pathlib import Path

REVIEWED = {
    "Les enfants se sont blottis *contre* leur mère.": "The children snuggled up *against* their mother.",
    "Je ne vous ai jamais *mieux* aimée.": "I have never loved you *more*.",
    "La *porte* de la cuisine grince terriblement.": "The kitchen *door* creaks terribly.",
    '"Je peux avoir ce sandwich à *emporter* ?"': '"Can I have this sandwich *to go*?"',
    "Dès ce jour nous vous passons *commande* pour cet ouvrage.": "As of today, we are placing an *order* with you for this work.",
    "L'autorité revenait à celui qui *remportait* la victoire.": "Authority belonged to whoever *won*.",
    "Marie a *protesté* de son innocence devant le juge.": "Marie *asserted* her innocence before the judge.",
    "Elles pourront frapper des groupes *ciblés*.": "They will be able to strike *targeted* groups.",
    "Le mot « étudiant » *dérive* du participe présent du verbe « étudier ».": "The word “étudiant” *derives* from the present participle of the verb “étudier”.",
    "J'ai toujours *haï* la campagne.": "I've always *hated* the countryside.",
    "Cette tablette de *chocolat* noir est délicieuse.": "This bar of dark *chocolate* is delicious.",
    "Le professeur a demandé une copie en *triple* exemplaire.": "The teacher asked for the document in *triplicate*.",
    "Vous feriez mieux de vous *abstenir*.": "You'd better *abstain*.",
    "Le *camion* de déménagement arrivera demain matin à huit heures.": "The *moving truck* will arrive tomorrow morning at eight.",
    "Les ouvriers utilisent un *engin* de levage pour déplacer les matériaux lourds.": "The workers use *lifting equipment* to move heavy materials.",
}


def repair_card(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    in_examples = False
    pair_pos = 0
    current_fr: str | None = None
    changed = False
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
        elif current_fr in REVIEWED:
            indent = line[: len(line) - len(line.lstrip())]
            newline = "\n" if raw.endswith("\n") else ""
            lines[i] = f"{indent}{REVIEWED[current_fr]}{newline}"
            changed = True
        pair_pos += 1
    if changed:
        path.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--paths-file", required=True)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    for rel in Path(args.paths_file).read_text(encoding="utf-8").splitlines():
        rel = rel.strip()
        if rel:
            repair_card(root / rel)


if __name__ == "__main__":
    main()
