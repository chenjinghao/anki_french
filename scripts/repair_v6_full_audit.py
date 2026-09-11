#!/usr/bin/env python3
"""Deterministic repairs for full-corpus hard-gate and semantic-audit findings.

This pass is intentionally path- and French-source-specific. It never performs
broad English substitutions, so reviewed fixes cannot leak into unrelated cards.
"""
from __future__ import annotations

import argparse
from pathlib import Path

EXAMPLES: dict[str, dict[str, str]] = {
    # Full 5,000-card hard-gate failures.
    "cards/0066_très.yml": {"J'ai été bonne? *Très, très* bonne.": "Was I good? *Very, very* good."},
    "cards/0082_après.yml": {"Et *après* ? Qu'est-ce que ça peut faire ?": "And *then*? What difference does it make?"},
    "cards/0088_venir.yml": {'"Alors, ça *vient* ? On n\'a pas toute la journée !"': '"Well, is it *coming*? We don\'t have all day!"'},
    "cards/0107_fort.yml": {'"*Fort* bien ! Nous ferons comme vous proposez."': '"*Very* well! We\'ll do as you suggest."'},
    "cards/0171_nom.yml": {'"*Nom d\'une pipe* ! J\'ai oublié mes clés."': '"*Good grief*! I forgot my keys."'},
    "cards/0194_meilleur.yml": {"Tu connais la *meilleure* ? J'ai gagné à la loterie !": "Want to hear the *best* part? I won the lottery!"},
    "cards/0267_loi.yml": {'"Tu te prends pour qui ? C\'est moi qui fais la *loi* ici !"': '"Who do you think you are? I make the *rules* here!"'},
    "cards/0354_importer.yml": {"Que lui *importent* les conséquences ? Il fait toujours ce qu'il veut.": "What do the consequences *matter* to him? He always does whatever he wants."},
    "cards/0510_toi.yml": {'"*Toi*, faire la cuisine ? Impossible !"': '"*You*, cooking? Impossible!"'},
    "cards/1338_manger.yml": {'"Tu l\'as vu ? Il la *mangeait* des yeux !"': '"Did you see him? He was *devouring her with his eyes*!"'},
    "cards/1876_maire.yml": {"L'*Oberbürgermeister* de Munich sera présent à la cérémonie.": "The *mayor* of Munich will be present at the ceremony."},
    "cards/1972_bonjour.yml": {"Voilà ma petite fille. *Bonjour*, ma chérie. Viens par ici.": "This is my little girl. *Hello*, sweetheart. Come here."},
    "cards/2086_dessiner.yml": {"Je ne sais pas *dessiner*. C'est une frustration.": "I don't know how to *draw*. It's frustrating."},
    "cards/2130_spécialement.yml": {"Vous aimez les chats ? Pas *spécialement*.": "Do you like cats? Not *particularly*."},
    "cards/2446_taxe.yml": {"Vous payez pas de *taxes*. Vous payez pas d'impôts.": "You don't pay any *taxes*. You don't pay any income tax."},
    "cards/2988_permis.yml": {"Vos papiers ? Pièce d'identité, *permis* de conduire.": "Your papers? ID, driver's *license*."},
    "cards/3313_assassinat.yml": {"Quiconque meurt de faim meurt d'un *assassinat*.": "Anyone who starves to death has been *killed*."},
    "cards/3610_planche.yml": {
        "Cette *planche* de Dürer vaut une fortune.": "This Dürer *print* is worth a fortune.",
        "La *planche* à repasser est dans la buanderie.": "The *ironing board* is in the laundry room.",
    },
    "cards/4189_grossir.yml": {"Tu ne veux pas *grossir* ? Ne mange pas trop de bonbons !": "You don't want to *gain weight*, do you? Don't eat too much candy!"},
    "cards/4564_bravo.yml": {"J'ai de bonnes nouvelles. *Bravo*. Vos appels ont porté leurs fruits.": "I've got good news. *Bravo*! Your calls paid off."},
    "cards/4582_sorcier.yml": {"Tu as vu comme il programme vite ? C'est un vrai *sorcier* en informatique !": "Did you see how fast he codes? He's a real computer *wizard*!"},

    # Highest-confidence whole-corpus semantic-audit findings.
    "cards/2846_alimentation.yml": {"Le rayon *alimentation* se trouve au rez-de-chaussée.": "The *food section* is on the ground floor."},
    "cards/1247_carrière.yml": {"Cette *carrière* encombrée n'offre plus de débouchés.": "This overcrowded *career field* no longer offers any prospects."},
    "cards/4070_envoler.yml": {"Les cours de la bourse se sont *envolés* cette semaine.": "Stock prices *soared* this week."},
    "cards/4868_affectation.yml": {"Il bâilla avec *affectation*.": "He yawned with *affectation*."},
    "cards/3106_décrocher.yml": {"Les actions ont *décroché* de façon spectaculaire.": "The shares *plunged* dramatically."},
    "cards/3212_détention.yml": {"La *détention* des effets de la succession est confiée au notaire.": "The notary is entrusted with *custody* of the estate's assets."},
    "cards/4980_solidaire.yml": {"Le guidon est rendu *solidaire* du cadre par deux vis.": "The handlebars are *secured* to the frame with two screws."},
    "cards/3508_creux.yml": {
        "Les périodes *creuses* permettent de faire des économies.": "*Off-peak* periods make it possible to save money.",
        "L'entreprise est dans le *creux* de la vague.": "The company is *in a slump*.",
    },
    "cards/1575_quart.yml": {"La partition contient plusieurs *quarts* de soupir.": "The score contains several *sixteenth rests*."},
    "cards/1358_attacher.yml": {"Les montgolfières sont *attachées* au sol.": "The hot-air balloons are *tethered* to the ground."},
    "cards/3755_piquer.yml": {"Les vers ont *piqué* toute la poutre.": "The worms have *riddled* the entire beam."},
    "cards/0015_ne.yml": {"Il *ne* s'en est fallu que d'un cheveu.": "It *only* missed by a hair."},
    "cards/3677_visiblement.yml": {"Il se tait, se domine *visiblement*.": "He falls silent, *visibly* controlling himself."},
    "cards/2296_cheveu.yml": {"Son explication est vraiment tirée par les *cheveux*.": "His explanation is really *far-fetched*."},
    "cards/1487_franchir.yml": {"Le randonneur a *franchi* le torrent à gué.": "The hiker *forded* the stream."},
    "cards/4292_mordre.yml": {"Il s'est facilement laissé *mordre* à l'hameçon de cette arnaque.": "He easily *took the bait* in this scam."},
    "cards/0912_somme.yml": {"Cette *somme* forfaitaire de la prévoyance est défiscalisée.": "This lump-sum benefit from the pension plan is *tax-exempt*."},
    "cards/3268_obéir.yml": {"Le gouvernail n'*obéit* plus.": "The rudder no longer *responds*."},
    "cards/4390_parer.yml": {"L'escrimeur a *paré* l'attaque avec élégance.": "The fencer *parried* the attack elegantly."},
    "cards/0942_franc.yml": {"L'arbitre a sifflé un coup *franc*.": "The referee awarded a *free kick*."},
    "cards/0299_coup.yml": {
        "L'arbitre a sifflé un *coup franc*.": "The referee awarded a *free kick*.",
        "Les enfants *ont échangé des coups* dans la cour de récréation.": "The children *traded blows* in the playground.",
    },
    "cards/0765_crise.yml": {"La *crise* de colique néphrétique l'a conduit aux urgences.": "A *bout* of renal colic sent him to the emergency room."},
    "cards/3623_virer.yml": {
        "Le manège *vire* sans arrêt depuis ce matin.": "The carousel has been *going around* nonstop since this morning.",
        "Le temps *vire* au beau.": "The weather is *turning fine*.",
    },
    "cards/3932_joue.yml": {"Les *joues* de la poulie sont en acier inoxydable.": "The pulley's *side plates* are made of stainless steel."},
    "cards/2768_vache.yml": {"C'est un *vache de* beau spectacle !": "That's one *hell of* a good show!"},
    "cards/3810_serré.yml": {"Son analyse était remarquablement *serrée*.": "His analysis was remarkably *rigorous*."},
    "cards/1008_mille.yml": {"Le tireur a mis en plein dans le *mille*.": "The shooter hit the *bull's-eye*."},
    "cards/3260_chair.yml": {"Cette poire a une *chair* fondante.": "This pear has *tender, melting flesh*."},
    "cards/4290_rat.yml": {"Cette *rate* défend férocement ses petits.": "This *female rat* fiercely defends her young."},
    "cards/4906_claquer.yml": {"Le fouet du dompteur *claque* dans l'arène.": "The tamer's whip *cracks* in the arena."},
    "cards/3437_manche.yml": {'"Il se débrouille comme un *manche*."': '"He\'s making a complete *mess* of it."'},
    "cards/3775_touche.yml": {
        "La *touche* verrouillage majuscule est allumée.": "The *Caps Lock key* is on.",
        "L'arbitre siffle la *touche*.": "The referee signals a *throw-in*.",
    },
    "cards/1497_vertu.yml": {"Cette tisane aurait des *vertus* apaisantes.": "This herbal tea is said to have *calming properties*."},
    "cards/3155_voile.yml": {
        "Le moniteur de *voile* nous explique les manœuvres.": "The *sailing instructor* explains the maneuvers to us.",
        "Le *voile* du palais peut causer des problèmes d'élocution.": "The *soft palate* can cause speech problems.",
    },
    "cards/4385_levée.yml": {"Une forte *levée* de houle est prévue dans la rade.": "A strong *swell* is forecast in the harbor."},
    "cards/1223_fil.yml": {"Je tiens tous les *fils* de cette intrigue.": "I've got all the *threads* of this plot."},
    "cards/0804_plaire.yml": {"*Plaise* au ciel que nous réussissions !": "*Heaven grant* that we succeed!"},
    "cards/4893_craquer.yml": {"Le parquet ancien *craque* à chaque pas.": "The old wooden floor *creaks* with every step."},
    "cards/3267_référer.yml": {"Pour plus d'informations, veuillez vous *référer* au mode d'emploi.": "For more information, please *refer* to the instructions."},
    "cards/4089_sursis.yml": {"Le tribunal a accordé un *sursis* avec mise à l'épreuve.": "The court granted a *suspended sentence with probation*."},
    "cards/4832_serre.yml": {"Le hibou grand-duc a des *serres* puissantes.": "The eagle-owl has powerful *talons*."},
    "cards/4051_sou.yml": {"Les enfants mettaient leurs *sous* dans une tirelire.": "The children put their *coins* in a piggy bank."},
    "cards/3833_brandir.yml": {"Le menuisier a *brandi* le chevron sur la panne avec une cheville en bois.": "The carpenter *fastened* the rafter to the purlin with a wooden peg."},
    "cards/2127_radical.yml": {"Le *radical* du mot \"chanter\" est \"chant\".": "The *stem* of the word \"chanter\" is \"chant\"."},
    "cards/1283_qualifier.yml": {"L'adjectif 'rouge' *qualifie* le nom 'voiture'.": "The adjective 'rouge' *modifies* the noun 'voiture'."},
    "cards/0114_pays.yml": {"Nous vivons dans un *pays de cocagne*.": "We live in a *land of plenty*."},
    "cards/0033_ou.yml": {"La coccinelle, *ou* bête à bon Dieu, est considérée comme un porte-bonheur.": "The ladybug, *or* 'God's little creature,' is considered a good-luck charm."},
    "cards/0416_base.yml": {"Le mot \"chanter\" a pour *base* \"chant\".": "The word \"chanter\" has the *base* \"chant\"."},
    "cards/1141_honneur.yml": {"L'*honneur* est sauf.": "*Honor* is intact."},
    "cards/3967_panne.yml": {"La charpente repose sur une *panne* en acier.": "The roof frame rests on a steel *purlin*."},
    "cards/3292_chantier.yml": {'"*CHANTIER* INTERDIT AU PUBLIC"': '"*CONSTRUCTION SITE* — NO PUBLIC ACCESS"'},
    "cards/4157_dérive.yml": {"L'économie du pays est en pleine *dérive*.": "The country's economy is *drifting out of control*."},
    "cards/1385_côte.yml": {"Les *côtes* de bettes sont excellentes cuites à la vapeur.": "The *stalks* of Swiss chard are excellent steamed."},
    "cards/3015_gueule.yml": {'"Cette exposition *a de la gueule*!"': '"This exhibition *looks fantastic*!"'},
    "cards/1450_dénoncer.yml": {"Le lanceur d'alerte s'est *dénoncé* publiquement.": "The whistleblower *came forward* publicly."},
    "cards/0604_article.yml": {"Les *articles* pour hommes sont en solde.": "Men's *items* are on sale."},
    "cards/1761_chute.yml": {"La *chute* des reins est une zone sensible du corps.": "The *small of the back* is a sensitive area of the body."},
    "cards/2347_arracher.yml": {"Les critiques s'*arrachent* le dernier film de ce réalisateur.": "Critics are *clamoring to see* this director's latest film."},
    "cards/2081_désoler.yml": {
        "Les pillards ont *désolé* la campagne environnante.": "The raiders *devastated* the surrounding countryside.",
        "Son air *désolé* ne trompait personne.": "The *sorry* expression fooled no one.",
    },
    "cards/1856_progresser.yml": {"Son état de santé *progresse* de jour en jour.": "His health is *improving* day by day."},
    "cards/4895_crête.yml": {"Le dindon gonfle sa *crête* pour impressionner les femelles.": "The turkey puffs up its *crest* to impress the females."},
    "cards/3071_déborder.yml": {"La haie *déborde* sur le trottoir.": "The hedge *encroaches* on the sidewalk."},
    "cards/2357_remise.yml": {"Il faut ranger la tondeuse dans la *remise* après utilisation.": "The mower should be stored in the *shed* after use."},
    "cards/3255_queue.yml": {"Les *queues* de ces cerises sont parfaites pour la tisane.": "The *stems* of these cherries are perfect for herbal tea."},
    "cards/2068_seuil.yml": {"Un nouveau paillasson décore le *seuil* de leur maison.": "A new doormat decorates the *threshold* of their house."},
    "cards/4264_titulaire.yml": {"Marie est devenue *titulaire* après sa période d'essai.": "Marie got a *permanent position* after her probationary period."},
    "cards/4088_débit.yml": {"Ces articles ont un excellent *débit* pendant les soldes.": "These items *sell very well* during the sales."},
    "cards/0483_cadre.yml": {"Le petit chalet est niché dans un *cadre* de verdure.": "The little cottage is nestled in a *green setting*."},
    "cards/0626_pied.yml": {"Le cavalier a *mis pied à terre* devant l'auberge.": "The rider *dismounted* in front of the inn."},
    "cards/1269_pensée.yml": {"Les *pensées* printanières égaient le jardin.": "The spring *pansies* brighten the garden."},
    "cards/4587_déplaire.yml": {"Je ne me *déplais* pas du tout dans ma nouvelle ville.": "I *quite like* my new city."},
    "cards/1076_puissance.yml": {"Cette nouvelle technologie décuple notre *puissance* de production.": "This new technology *increases our production capacity tenfold*."},
    "cards/3028_rattraper.yml": {"Le coureur a *rattrapé* le peloton après une crevaison.": "The rider *caught up with the pack* after a puncture."},
    "cards/4779_forger.yml": {"Le bijoutier *forge* délicatement l'alliance en or.": "The jeweler carefully *forges* the gold wedding ring."},
    "cards/0182_vers.yml": {"Ces *vers* alternés créent un rythme intéressant.": "These alternating *lines of verse* create an interesting rhythm."},
    "cards/1846_alliance.yml": {"Le bijoutier a gravé leurs initiales sur leurs *alliances*.": "The jeweler engraved their initials on their *wedding rings*."},
    "cards/1795_essence.yml": {"Il faut faire attention en manipulant l'*essence* de térébenthine.": "Be careful when handling *turpentine*."},
    "cards/4006_planer.yml": {"Le menuisier *plane* soigneusement la planche.": "The carpenter carefully *planes* the board."},
    "cards/0792_message.yml": {"Le *message* a été remis en mains propres.": "The *message* was hand-delivered."},
    "cards/3927_loup.yml": {"La *louve* allaite ses petits dans la tanière.": "The *she-wolf* nurses her cubs in the den."},
}

DEFINITIONS = {
    "cards/0461_commission.yml": "commission; committee",
    "cards/4350_gestionnaire.yml": "manager; administrator",
}

TEXT_REPLACEMENTS = {
    "cards/0598_rue.yml": {
        "It corresponds to the German word Straße or Gasse and refers to smaller roads surrounded by buildings and used mainly by pedestrians and local traffic.":
            "It is the usual French word for an urban street, especially one lined with buildings and used by local traffic and pedestrians.",
        "<span class=\"fr\">Route</span> It can be compared to the German Chaussee or Landstraße and is commonly used for roads connecting towns and on which higher speeds are permitted.":
            "<span class=\"fr\">Route</span> usually refers to a road or route connecting places, often outside dense urban areas and suitable for faster traffic.",
    }
}


def _example_bounds(lines: list[str]) -> tuple[int, int]:
    start = next(i for i, line in enumerate(lines) if line.startswith("Beispielsätze:")) + 1
    end = next((i for i in range(start, len(lines)) if lines[i].startswith("# Notes")), len(lines))
    return start, end


def replace_examples(text: str, path: str, replacements: dict[str, str], *, check_only: bool = False) -> tuple[str, list[str]]:
    lines = text.splitlines()
    errors: list[str] = []
    try:
        start, end = _example_bounds(lines)
    except StopIteration:
        return text, [f"{path}: missing Beispielsätze block"]
    for fr, expected in replacements.items():
        hits = [i for i in range(start, end - 1) if lines[i].strip() == fr]
        if len(hits) != 1:
            errors.append(f"{path}: expected one French source hit, found {len(hits)}: {fr}")
            continue
        i = hits[0]
        if check_only:
            if lines[i + 1].strip() != expected:
                errors.append(f"{path}: semantic repair regression: {fr} -> {lines[i + 1].strip()}")
        else:
            indent = lines[i + 1][: len(lines[i + 1]) - len(lines[i + 1].lstrip())]
            lines[i + 1] = indent + expected
    return "\n".join(lines) + ("\n" if text.endswith("\n") else ""), errors


def replace_definition(text: str, path: str, expected: str, *, check_only: bool = False) -> tuple[str, list[str]]:
    lines = text.splitlines()
    errors: list[str] = []
    try:
        i = next(i for i, line in enumerate(lines) if line.startswith("Definition:"))
        j = next(j for j in range(i + 1, len(lines)) if lines[j].startswith("Register:"))
    except StopIteration:
        return text, [f"{path}: malformed Definition/Register block"]
    current = lines[i][len("Definition:"):].strip()
    if check_only:
        if current != expected or j != i + 1:
            errors.append(f"{path}: definition repair regression: {current!r}")
        return text, errors
    lines[i:j] = [f"Definition: {expected}"]
    return "\n".join(lines) + ("\n" if text.endswith("\n") else ""), errors


def process(root: Path, *, check_only: bool = False) -> list[str]:
    errors: list[str] = []
    touched = set(EXAMPLES) | set(DEFINITIONS) | set(TEXT_REPLACEMENTS)
    for rel in sorted(touched):
        file = root / rel
        if not file.exists():
            errors.append(f"{rel}: missing card")
            continue
        text = file.read_text(encoding="utf-8")
        if rel in EXAMPLES:
            text, e = replace_examples(text, rel, EXAMPLES[rel], check_only=check_only)
            errors.extend(e)
        if rel in DEFINITIONS:
            text, e = replace_definition(text, rel, DEFINITIONS[rel], check_only=check_only)
            errors.extend(e)
        for old, new in TEXT_REPLACEMENTS.get(rel, {}).items():
            if check_only:
                if old in text or new not in text:
                    errors.append(f"{rel}: reviewed note repair regression")
            else:
                count = text.count(old)
                if count != 1:
                    errors.append(f"{rel}: expected one note fragment hit, found {count}")
                else:
                    text = text.replace(old, new)
        if not check_only:
            file.write_text(text, encoding="utf-8")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--report")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    errors = process(root, check_only=args.check)
    mode = "CHECK" if args.check else "REPAIR"
    lines = [
        f"V6 FULL-CORPUS AUDIT {mode}",
        f"Reviewed cards: {len(set(EXAMPLES) | set(DEFINITIONS) | set(TEXT_REPLACEMENTS))}",
        f"Reviewed example repairs: {sum(len(v) for v in EXAMPLES.values())}",
        f"Errors: {len(errors)}",
    ]
    if errors:
        lines += ["", "ERRORS"] + [f"- {e}" for e in errors]
    output = "\n".join(lines) + "\n"
    print(output, end="")
    if args.report:
        Path(args.report).write_text(output, encoding="utf-8")
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
