#!/usr/bin/env python3
"""Source-aware deterministic repairs for v6 scale validation.

Repairs are keyed by preserved French learner sentences or card paths, not by a
particular model output. This keeps reviewed semantic fixes stable across model
revisions while preserving French source lines and compatibility-sensitive keys.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

REVIEWED = {
    "Les enfants se sont blottis *contre* leur mère.": "The children snuggled up *against* their mother.",
    "Le petit chat s'est blotti *contre* moi.": "The little cat snuggled up *against* me.",
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

    # Multi-sentence completeness regressions found in the 500-card sample.
    '"Tu as dormi toute la *matinée* ? Tu as manqué un temps magnifique !"': '"Did you sleep all *morning*? You missed beautiful weather!"',
    "As-tu déjà goûté le guacamole? C'est fait avec des *avocats*.": "Have you ever tasted guacamole? It's made with *avocados*.",
    '"Alors Marie, *on* s\'en va déjà ? La soirée ne fait que commencer !"': '"So, Marie, are *we* leaving already? The party has only just begun!"',
    '"C\'est la *honte* ! Je n\'arrive pas à croire que j\'ai raté l\'examen."': '"What a *shame*! I can\'t believe I failed the exam."',
    "*Comme* c'est cher ! Je ne peux pas me le permettre.": "*How* expensive it is! I can't afford it.",
    "Il veut *nous* voir, *nous*! Quelle surprise!": "He wants to see *us*—us! What a surprise!",
    "Il veut *nous* aider, *nous*? C'est inattendu.": "He wants to help *us*—us? That's unexpected.",
    "C'est à *nous*! Notre tour est enfin arrivé.": "It's *our* turn! Our turn has finally come.",
    "*Et* comment ! Je suis tout à fait d'accord.": "*Absolutely*! I completely agree.",
    '"C\'était moins *une* ! J\'ai failli rater mon train."': '"*That was close*! I almost missed my train."',
    "Tu as *retrouvé* mes clés ? Je les cherche partout !": "Did you *find* my keys? I've been looking everywhere for them!",
    "Cette situation est inacceptable. *Enfin*, c'est mon opinion.": "This situation is unacceptable. *Anyway*, that's my opinion.",
    "*Enfin*, parle ! Qu'est-ce qui s'est passé ?": "*Come on*, speak! What happened?",
    "*Enfin*, à quoi penses-tu ? Ce n'est pas raisonnable !": "*Come on*, what are you thinking? That's not reasonable!",
    "Pensez-vous encore à Jean ? — J'*y* pense souvent.": "Do you still think of Jean? — I think *about him* often.",
    "De quel *côté* venez-vous ? Je vous attendais de l'autre direction.": "Which *way* are you coming from? I was expecting you from the other direction.",
    "Tu as fini tes devoirs ? – Euh... *enfin*... pas encore.": "Did you finish your homework? — Uh... *well*... not yet.",
    "*Comme* il dit cela ! On dirait un poète.": "*The way* he says that! He sounds like a poet.",
    "Louis a-t-il ses clés ? Je ne veux pas qu'*il* reste dehors.": "Does Louis have his keys? I don't want *him* to be locked out.",
    "Le courrier est-*il* arrivé ? J'attends un colis important.": "Has the mail arrived? I'm expecting an important package.",
    "J'étais fou amoureux. *Elle* m'aimait bien.": "I was madly in love. *She* liked me.",
    "*On* a frappé à la porte. Peux-tu aller ouvrir ?": "Someone knocked at the door. Can you go answer it?",
    "T'as vu mon *triple* saut ? Je peux le refaire.": "Did you see my *triple* jump? I can do it again.",

    # Wrong-sense / fluency regressions found during manual review.
    "Le chien a retrouvé *son* collier sous le canapé.": "The dog found *its collar* under the couch.",
    "Il pleure *tant* qu'il ne peut plus parler.": "He cries *so much* that he can no longer speak.",
    "Le *soir* tombe déjà en hiver.": "Night falls early *in the evening* in winter.",
    '"Je suis vraiment du *soir*, je ne peux pas dormir avant minuit."': '"I\'m really a *night owl*; I can\'t sleep before midnight."',
    "Le chef d'orchestre *dirigeait* la symphonie avec passion.": "The conductor *conducted* the symphony passionately.",
    "L'*arme* blanche est interdite dans les lieux publics.": "Carrying an *edged weapon* is prohibited in public places.",
    "Elle a *remonté* sa jupe qui glissait.": "She *pulled up* her skirt as it slipped down.",
    "En 1978, la gauche échoue aux *législatives*.": "In 1978, the left lost the *legislative elections*.",
    '"C\'est un problème *de taille*!"': '"It\'s a *major* problem!"',
    "Sous la *menace* d'une arme, elle a dû ouvrir le coffre-fort.": "At *gunpoint*, she had to open the safe.",
    "Cette voiture *dépense* trop d'essence pour moi.": "This car *uses* too much fuel for me.",
    "Les enfants doivent se *dépenser* dans le jardin.": "The children need to *burn off energy* in the garden.",
    "Les banques ont été *contraintes* de fermer leurs guichets.": "The banks were *forced* to close their counters.",
    "Le *onze* national a remporté la victoire.": "The national *eleven* won the match.",
    "Dans cette équation, le *paramètre* a représente la pente de la droite.": "In this equation, *parameter* a represents the slope of the line.",
    "Le sel *use* rapidement les carrosseries des voitures.": "Salt quickly *wears away* car bodies.",
    "Cette copie d'examen nécessite une double *vérification*.": "This exam paper needs to be *double-checked*.",
    "Votre père lève les *pouces* pour dire bravo.": "Your father gives a *thumbs-up* to show approval.",
    '"Je me suis *tourné les pouces* toute la journée."': '"I *twiddled my thumbs* all day."',
    "Les manifestants ont *bombardé* la voiture du ministre avec des œufs.": "The protesters *pelted* the minister's car with eggs.",
    "Donne-moi quelque chose pour *envelopper* le petit.": "Give me something to *wrap the baby in*.",
    "Il était *rémunéré* par une excellente nourriture.": "He was *paid* with excellent food.",
    "Le *montage* de ma nouvelle bibliothèque m'a pris trois heures.": "It took me three hours to *assemble* my new bookcase.",
    "Le grand chêne s'est *écroulé* sur la route.": "The large oak *fell* across the road.",
    '"Il est parti *au triple galop* !"': '"He took off *at full gallop*!"',
    "Cette erreur compte *triple* dans l'évaluation finale.": "This error *counts three times* in the final assessment.",
    "Je vous envoie ce document en *triple* copie.": "I'm sending you *three copies* of this document.",
    "Elle a mis un temps *triple* pour finir l'exercice.": "It took her *three times as long* to finish the exercise.",
}

DEFINITION_REVIEWED = {
    "cards/0035_leur.yml": "their; to them",
    "cards/0732_ceci.yml": "this; [indefinite demonstrative pronoun]",
    "cards/1703_conséquent.yml": "consistent; substantial; therefore (par conséquent)",
    "cards/1775_nier.yml": "to deny",
    "cards/2051_dépenser.yml": "to spend; consume; expend",
    "cards/2327_purement.yml": "purely",
    "cards/2506_aggraver.yml": "to worsen; aggravate",
    "cards/2518_capitaine.yml": "captain",
    "cards/3000_user.yml": "to wear out; use",
    "cards/3561_déceler.yml": "to detect; discover",
    "cards/3657_politiquement.yml": "politically",
    "cards/4077_yougoslave.yml": "Yugoslav",
    "cards/4233_arrivant.yml": "newcomer; arrival",
    "cards/4329_bombarder.yml": "to bomb; bombard",
    "cards/4425_dissoudre.yml": "to dissolve",
    "cards/4532_bosser.yml": "to work; study hard [informal]",
    "cards/4796_rémunérer.yml": "to pay; remunerate",
    "cards/4856_questionner.yml": "to question",
    "cards/4904_montage.yml": "assembly; editing",
}


def replace_definition(text: str, value: str) -> str:
    """Replace scalar or block-scalar Definition with one reviewed scalar line."""
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


def dedupe_definition(text: str) -> str:
    """Collapse exact repeated glosses introduced by short-fragment MT."""
    lines = text.splitlines(keepends=True)
    for i, raw in enumerate(lines):
        if not raw.startswith("Definition:"):
            continue
        value = raw.split(":", 1)[1].strip()
        if not value or value in {"|-", "|", ">-", ">"}:
            return text
        parts = re.split(r"([;,])", value)
        seen: set[str] = set()
        out: list[str] = []
        pending_sep = ""
        for part in parts:
            if part in {",", ";"}:
                pending_sep = part
                continue
            gloss = part.strip()
            if not gloss:
                continue
            key = re.sub(r"[^a-z0-9]+", " ", gloss.lower()).strip()
            if key in seen:
                continue
            if out:
                out.append((pending_sep or ";") + " ")
            out.append(gloss)
            seen.add(key)
            pending_sep = ""
        if out:
            newline = "\n" if raw.endswith("\n") else ""
            lines[i] = "Definition: " + "".join(out) + newline
        break
    return "".join(lines)


def repair_card(path: Path, rel: str) -> None:
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
    text = "".join(lines)
    if rel in DEFINITION_REVIEWED:
        text = replace_definition(text, DEFINITION_REVIEWED[rel])
    text = dedupe_definition(text)
    if changed or text != "".join(lines):
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
