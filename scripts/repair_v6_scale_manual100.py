#!/usr/bin/env python3
"""Reviewed repairs from the expanded 100-card manual sample."""
from __future__ import annotations

import argparse
from pathlib import Path

EXAMPLES = {
    "J'ai invité mes parents *et* mes beaux-parents pour Noël.": "I invited my parents *and* my parents-in-law for Christmas.",
    "Il a trouvé un trésor caché *dans* une vieille malle au grenier.": "He found a treasure hidden *in* an old trunk in the attic.",
    "C'est certain qu'on va *y* aller.": "I'm sure we're going *there*.",
    "Le restaurant se trouve à *deux* pas d'ici, on peut y aller à pied.": "The restaurant is just *a stone's throw* from here; we can walk there.",
    "Cette plante *craint* le gel.": "This plant is *sensitive to* frost.",
    "Le métal *chauffé à blanc* est dangereux à manipuler.": "*White-hot* metal is dangerous to handle.",
    "Le professeur a *souligné* les fautes d'orthographe en rouge.": "The teacher *underlined* the spelling mistakes in red.",
    "Elle *soulignait* toujours ses yeux d'un trait de crayon noir.": "She always *outlined* her eyes with black eyeliner.",
    "L'*attente* du train m'a semblé interminable.": "The *wait* for the train seemed endless.",
    "Les jeunes d'aujourd'hui montrent un fort *engagement* associatif.": "Young people today show strong *community involvement*.",
    "Les élèves apprennent la *division* en mathématiques dès l'école primaire.": "Students learn *division* in mathematics from primary school onward.",
    "La *taille* minimum pour ce manège est de 1,40 m.": "The minimum *height* for this ride is 1.40 metres.",
    "Le *siège* éjectable a sauvé la vie du pilote.": "The *ejection seat* saved the pilot's life.",
    "Ce sont eux qui *émettent* le plus de CO<sub>2</sub>.": "They are the ones who *emit* the most CO<sub>2</sub>.",
    "Pierre se *dépense* sans compter pour aider les autres.": "Pierre *spares no effort* to help others.",
    "Je fais tailler mes *arbres* pour donner de l'ombre.": "I have my *trees* pruned to provide shade.",
    "Le buvard *absorbe* l'encre rapidement.": "Blotting paper *absorbs* ink quickly.",
    "Marie a *branché* la conversation sur ses vacances.": "Marie *steered* the conversation toward her vacation.",
    '"Il a *ramassé* une bonne gifle !"': '"He *got* a hard slap!"',
    "Marie *ramasse* ses cheveux en chignon.": "Marie *gathers* her hair into a bun.",
    "Il allait demander ton *renvoi* de la police.": "He was going to ask for your *dismissal* from the police force.",
    "L'arbitre a sifflé un *renvoi* aux six mètres.": "The referee awarded a six-metre *goal kick*.",
    '"Il n\'y en a pas *épais* dans ton portefeuille !"': '"There\'s *not much* in your wallet!"',
    "Le médecin teste le *réflexe* rotulien avec un petit marteau.": "The doctor tests the *patellar reflex* with a small hammer.",
    "Le *réflexe* de succion est important chez les nouveau-nés.": "The *sucking reflex* is important in newborns.",
    "Les *réflexes* conditionnés s'acquièrent par l'apprentissage.": "*Conditioned reflexes* are acquired through learning.",
    "Le stationnement *unilatéral* est autorisé dans cette rue entre 8h et 18h.": "*One-sided parking* is allowed on this street between 8 a.m. and 6 p.m.",
    "Le *serveur* nous a apporté la carte des vins.": "The *waiter* brought us the wine list.",
    "Les *serveurs* portaient tous un nœud papillon noir.": "The *waiters* all wore black bow ties.",
    "Pierre est un excellent *serveur* au tennis.": "Pierre is an excellent *server* in tennis.",
    "Les sept *péchés* capitaux sont l'orgueil, l'avarice, la luxure, l'envie, la gourmandise, la colère et la paresse.": "The seven deadly *sins* are pride, greed, lust, envy, gluttony, wrath, and sloth.",
    '"Le chocolat, c\'est mon *péché* mignon."': '"Chocolate is my *guilty pleasure*."',
    "Pierre fait la *traversée* du lac tous les matins à la nage.": "Pierre *swims across* the lake every morning.",
    "Au *détour* du chemin, nous avons aperçu un magnifique château.": "Around a *bend* in the path, we caught sight of a magnificent castle.",
    "En physique, l'*accélération* se mesure en mètres par seconde carrée.": "In physics, *acceleration* is measured in metres per second squared.",
    "La salle de *réveil* était calme et bien éclairée.": "The *recovery room* was quiet and well lit.",
    "Les infirmières surveillent attentivement les patients en salle de *réveil*.": "The nurses carefully monitor patients in the *recovery room*.",
    "Un énorme rocher s'est *écroulé* dans la vallée.": "A huge rock *fell* into the valley.",
}

DEFINITIONS = {
    "cards/0016_sur.yml": "on; over; about",
    "cards/0031_nous.yml": "we; us",
    "cards/0036_y.yml": "there; to it",
    "cards/0120_suivre.yml": "to follow; track; attend",
    "cards/0237_propre.yml": "clean; own; proper",
    "cards/0500_craindre.yml": "to fear; be afraid of",
    "cards/0540_diriger.yml": "to lead; direct; manage",
    "cards/0600_bref.yml": "brief; short; in short",
    "cards/0660_date.yml": "date",
    "cards/0816_souligner.yml": "to underline; emphasize",
    "cards/0876_supérieur.yml": "superior; higher; supervisor",
    "cards/0936_attente.yml": "waiting; wait",
    "cards/0996_officiel.yml": "official",
    "cards/1042_engagement.yml": "commitment; engagement",
    "cards/1092_maître.yml": "master; teacher; owner",
    "cards/1380_démocratique.yml": "democratic",
    "cards/1440_division.yml": "division; distribution",
    "cards/1500_taille.yml": "size; height; pruning",
    "cards/1631_fonctionnaire.yml": "civil servant; public official",
    "cards/1691_sexe.yml": "sex; gender",
    "cards/1739_monétaire.yml": "monetary",
    "cards/1787_émettre.yml": "to emit; issue; express",
    "cards/1847_préoccupation.yml": "concern; worry",
    "cards/2003_joueur.yml": "player; playful",
    "cards/2111_arbre.yml": "tree",
    "cards/2171_dignité.yml": "dignity",
    "cards/2231_incroyable.yml": "incredible; unbelievable",
    "cards/2279_cérémonie.yml": "ceremony",
    "cards/2339_certitude.yml": "certainty",
    "cards/2399_promouvoir.yml": "to promote",
    "cards/2459_collaborateur.yml": "colleague; coworker; contributor",
    "cards/2554_respectif.yml": "respective",
    "cards/2734_interdiction.yml": "prohibition; ban",
    "cards/2782_universitaire.yml": "university; academic",
    "cards/3022_absorber.yml": "to absorb; take in",
    "cards/3130_cibler.yml": "to target",
    "cards/3190_horrible.yml": "horrible; awful",
    "cards/3310_brancher.yml": "to connect; plug in; be interested in [informal]",
    "cards/3370_ramasser.yml": "to pick up; gather; collect",
    "cards/3427_dériver.yml": "to derive; drift; divert",
    "cards/3513_via.yml": "via; through",
    "cards/3573_publicitaire.yml": "advertising; promotional",
    "cards/3624_facilité.yml": "ease; aptitude; facility",
    "cards/3681_renvoi.yml": "dismissal; return; reference; goal kick",
    "cards/3789_épais.yml": "thick; dense",
    "cards/3909_terriblement.yml": "terribly",
    "cards/4017_yen.yml": "yen",
    "cards/4317_unilatéral.yml": "unilateral",
    "cards/4377_serveur.yml": "server; waiter; waitress",
    "cards/4437_péché.yml": "sin",
    "cards/4592_désireux.yml": "eager; desirous",
    "cards/4652_traversée.yml": "crossing",
    "cards/4712_regroupement.yml": "grouping; consolidation",
    "cards/4820_détour.yml": "detour; diversion",
    "cards/4940_réveil.yml": "alarm clock; awakening",
    "cards/5000_écrouler.yml": "to collapse; fall down",
}


def replace_definition(text: str, value: str) -> str:
    lines = text.splitlines(keepends=True)
    start = next((i for i, line in enumerate(lines) if line.startswith("Definition:")), None)
    if start is None:
        return text
    end = start + 1
    while end < len(lines):
        if lines[end].strip() and not lines[end].startswith((" ", "\t")):
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
