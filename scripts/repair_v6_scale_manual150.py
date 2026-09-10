#!/usr/bin/env python3
"""Reviewed repairs from the full 150-card manual sample.

Includes source-aware preservation of common French proper names, fixes for the
remaining polysemy/idiom errors, and a robust repair for the card-0002 de note.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

EXAMPLES = {
    "Nous sommes passés *par* la côte pour arriver plus vite.": "We went *via* the coast to get there faster.",
    "Où suis-*je* ? *Je* ne reconnais pas cet endroit.": "Where am I? I don't recognize this place.",
    "Elle est grande *pour* son âge.": "She's tall *for* her age.",
    '"*Elle*, monter une entreprise ? Je n\'arrive pas à y croire !"': '"*Her*, start a business? I can\'t believe it!"',
    "Mettez un *point* à la fin de cette phrase.": "Put a *period* at the end of this sentence.",
    "Il faut *croire* que le train est en retard.": "Apparently, the train is late.",
    "N'en fais pas *trop* avec les décorations de Noël.": "Don't *overdo* the Christmas decorations.",
    "Le public a *rappelé* les artistes sur scène.": "The audience *called the performers back* on stage.",
    "Cet enfant est maintenant *propre*, il n'a plus besoin de couches.": "This child is now *toilet-trained* and no longer needs diapers.",
    "Le robinet *perd* de l'eau depuis ce matin.": "The faucet has been *leaking* since this morning.",
    "Je dois passer au *pressing* chercher mon costume.": "I have to stop by the *dry cleaner's* to pick up my suit.",
    "Le soleil *entrait* doucement par les fenêtres.": "Sunlight *streamed* gently through the windows.",
    "Son fils la *dépasse* maintenant d'une tête.": "Her son is now a head *taller* than she is.",
    "La *somme* totale s'élève à 1 250 euros.": "The *total* comes to €1,250.",
    "Elle tenait de notre père une *disposition* mélancolique.": "She inherited a melancholy *disposition* from our father.",
    "Les odeurs de cuisine *remontent* de la rue.": "Cooking smells *drift up* from the street.",
    "Il n'*emporte* jamais rien avec lui quand il voyage.": "He never *takes* anything with him when he travels.",
    "La rivière a *emporté* le petit pont en bois.": "The river *swept away* the little wooden bridge.",
    "Il devient donc impératif de pouvoir *bénéficier* de plus d'argent.": "It therefore becomes essential to *have access to* more funding.",
    "Le docteur Martin *consulte* tous les jours de 9h à 17h.": "Dr. Martin *sees patients* every day from 9 a.m. to 5 p.m.",
    "Je préfère boire mon café *pur*, sans sucre ni lait.": "I prefer my coffee *black*, without sugar or milk.",
    "Elle *descend* de son cheval avec élégance.": "She *dismounts* gracefully from her horse.",
    "Dans la plus *stricte* intimité, ils se sont mariés hier.": "They were married yesterday in the *strictest privacy*.",
    '"Ce n\'est qu\'un travail *alimentaire* pour moi, je rêve de devenir artiste."': '"It\'s just a *day job* for me; I dream of becoming an artist."',
    "L'année suivante, j'ai *rédigé* mon mémoire.": "The following year, I *wrote* my thesis.",
    "Mon frère travaille comme *éditeur* de logiciels depuis dix ans.": "My brother has worked for ten years as a software *publisher*.",
    "La société *éditrice* de films a remporté plusieurs prix.": "The film *production company* has won several awards.",
    "Le gouvernement encourage l'*immigration* choisie des travailleurs qualifiés.": "The government encourages *selective immigration* of skilled workers.",
    "Le gouvernement *fait la sourde oreille*.": "The government *turns a deaf ear*.",
    "La *poésie* en dialecte est une forme d'expression culturelle importante.": "*Poetry in dialect* is an important form of cultural expression.",
    "Le Premier ministre a demandé un remaniement *ministériel* urgent.": "The Prime Minister called for an urgent *cabinet reshuffle*.",
    "La crise *ministérielle* a été évitée de justesse.": "The *ministerial crisis* was narrowly avoided.",
    "L'élève devra répondre à une *interrogation* écrite de mathématiques demain.": "The student will have a written mathematics *test* tomorrow.",
    "L'*épisode* comique au milieu du drame a fait rire tout le public.": "The *comic episode* in the middle of the drama made the whole audience laugh.",
    "Elle a mis beaucoup de *hâte* dans ses préparatifs de voyage.": "She *hurried* through her travel preparations.",
    "La liaison par *faisceau hertzien* permet une communication rapide entre les stations.": "A *microwave relay link* enables rapid communication between the stations.",
    "Le jardinier a préparé un *faisceau* de brindilles pour allumer le feu.": "The gardener prepared a *bundle* of twigs to light the fire.",
    "Les soldats ont formé un *faisceau* avec leurs fusils pendant la pause.": "The soldiers *stacked their rifles* during the break.",
    "Cela permettait aussi de *ménager* la surprise.": "This also helped *preserve* the surprise.",
    "Il faut *ménager* ses forces pour la compétition de demain.": "You need to *conserve your strength* for tomorrow's competition.",
    "Cet *escalier* en bois craque quand on marche dessus.": "This wooden *staircase creaks* when you walk on it.",
    "Il faut *allonger* cette jupe, elle est trop courte.": "We need to *lengthen* this skirt; it's too short.",
    "La *franchise* dans cette assurance est de 500 euros.": "The *deductible* on this insurance policy is €500.",
    "Le médecin a *attesté* que Marie était en bonne santé.": "The doctor *certified* that Marie was in good health.",
    "J'ai oublié d'*essuyer* la vaisselle après le dîner.": "I forgot to *dry* the dishes after dinner.",
    "Notre équipe a dû *essuyer* une défaite contre les champions en titre.": "Our team had to *suffer* a defeat against the defending champions.",
    "Je me suis fait *haïr* de mes voisins à cause de ma musique trop forte.": "My neighbors came to *hate* me because my music was too loud.",
    "Pierre se *hait* d'avoir menti à sa mère.": "Pierre *hates himself* for lying to his mother.",
    "Les deux sœurs se *haïssent* depuis leur dispute sur l'héritage.": "The two sisters have *hated each other* since their argument over the inheritance.",
    "Le juge lui a accordé un *sursis* pour des raisons de santé.": "The judge granted him a *reprieve* for health reasons.",
    "Elle a obtenu un *sursis* de trois mois pour rembourser ses dettes.": "She was granted a three-month *extension* to repay her debts.",
    '"Ce vieux commerce est en *sursis* depuis des années."': '"This old business has been *living on borrowed time* for years."',
    "Le tribunal a prononcé deux ans de prison avec *sursis*.": "The court handed down a two-year *suspended sentence*.",
    "Le ministre *délégué* aux Affaires étrangères participera à la conférence.": "The *minister delegate* for Foreign Affairs will attend the conference.",
    "Pierre a été nommé *délégué* du personnel le mois dernier.": "Pierre was appointed an employee *representative* last month.",
    "Elle pissait et *chiait* partout.": "She was pissing and *shitting* everywhere.",
    "Je n'ai jamais vu un film aussi *nul à chier*.": "I've never seen a movie this *fucking awful*.",
    "*Ça va chier* si on continue comme ça !": "*All hell will break loose* if this keeps up!",
    "Elle ne supporte plus son boulot, elle se fait *chier* à mourir.": "She can't stand her job anymore; she's *bored shitless*.",
    "Les mauvaises habitudes alimentaires peuvent être changées par la *substitution* progressive d'aliments sains.": "Bad eating habits can be changed by gradually *substituting healthy foods*.",
    "J'ai mis tous les couverts sales dans le *panier* du lave-vaisselle.": "I put all the dirty *cutlery* in the dishwasher basket.",
    "Ma grand-mère range toujours son fil et ses aiguilles dans son *panier* à ouvrage.": "My grandmother always keeps her thread and needles in her *work basket*.",
    "Elle portait un *micro*-cravate discret pendant l'interview.": "She wore a discreet *lapel microphone* during the interview.",
    "Le *savoir-faire* se transmet souvent de génération en génération.": "*Know-how* is often passed down from generation to generation.",
    "Ils avaient tous le crâne *rasé*.": "They all had *shaved heads*.",
    "L'avion *rasait* le sol en volant.": "The plane was *flying close to the ground*.",
}

DEFINITIONS = {
    "cards/0004_à.yml": "to; at; in",
    "cards/0024_tout.yml": "all; every; whole",
    "cards/0028_autre.yml": "other; another",
    "cards/0038_elle.yml": "she; her",
    "cards/0061_me.yml": "me; myself",
    "cards/0135_croire.yml": "to believe; think",
    "cards/0167_ici.yml": "here",
    "cards/0217_mieux.yml": "better; best",
    "cards/0250_perdre.yml": "to lose",
    "cards/0289_système.yml": "system",
    "cards/0337_entrer.yml": "to enter; go in",
    "cards/0385_défendre.yml": "to defend; forbid",
    "cards/0409_réaliser.yml": "to realize; carry out; make",
    "cards/0433_intérieur.yml": "interior; inside; inner",
    "cards/0504_oublier.yml": "to forget",
    "cards/0535_placer.yml": "to place; put",
    "cards/0612_erreur.yml": "error; mistake",
    "cards/0685_dépasser.yml": "to exceed; overtake; go beyond",
    "cards/0912_somme.yml": "sum; amount",
    "cards/0948_disposition.yml": "arrangement; provision; disposition",
    "cards/1020_remonter.yml": "to go back up; raise; date back",
    "cards/1128_emporter.yml": "to take away; carry off",
    "cards/1164_moteur.yml": "engine; motor",
    "cards/1248_voter.yml": "to vote; pass (a law)",
    "cards/1272_bénéficier.yml": "to benefit from; enjoy",
    "cards/1392_inquiet.yml": "worried; anxious; uneasy",
    "cards/1476_sourire.yml": "to smile; smile",
    "cards/1523_accroître.yml": "to increase; grow",
    "cards/1595_consulter.yml": "to consult; look up; see a doctor",
    "cards/1643_pur.yml": "pure; plain",
    "cards/1705_descendre.yml": "to go down; get off; descend",
    "cards/1811_communautaire.yml": "community; EU/Community-related",
    "cards/2000_combler.yml": "to fill; make up for",
    "cards/2027_secondaire.yml": "secondary; side",
    "cards/2063_gouverner.yml": "to govern",
    "cards/2099_alimentaire.yml": "food; dietary",
    "cards/2135_rédiger.yml": "to draft; write",
    "cards/2183_éditeur.yml": "publisher; editor",
    "cards/2291_mobile.yml": "mobile; movable",
    "cards/2375_soupçonner.yml": "to suspect",
    "cards/2495_amoureux.yml": "in love; lover",
    "cards/2516_tenant.yml": "holder; supporter",
    "cards/2542_camion.yml": "truck",
    "cards/2626_paramètre.yml": "parameter; setting",
    "cards/2662_antérieur.yml": "previous; earlier; anterior",
    "cards/2710_persister.yml": "to persist",
    "cards/2770_aise.yml": "ease; comfortable",
    "cards/2854_sourd.yml": "deaf; muffled",
    "cards/3034_ministériel.yml": "ministerial",
    "cards/3274_identification.yml": "identification",
    "cards/3460_hâte.yml": "haste; eagerness",
    "cards/3490_faisceau.yml": "beam; bundle",
    "cards/3813_allonger.yml": "to lengthen; lie down",
    "cards/3861_franchise.yml": "frankness; deductible; franchise",
    "cards/3933_attester.yml": "to attest; certify; testify",
    "cards/3933_essuyer.yml": "to wipe; dry; suffer",
    "cards/3981_haïr.yml": "to hate",
    "cards/4005_insulte.yml": "insult",
    "cards/4041_ralentissement.yml": "slowdown; slowing",
    "cards/4089_sursis.yml": "reprieve; suspension; extension",
    "cards/4125_médiocre.yml": "mediocre; poor; average",
    "cards/4161_délégué.yml": "delegate; representative",
    "cards/4209_sphère.yml": "sphere; realm; area",
    "cards/4245_chier.yml": "to shit [vulgar]",
    "cards/4269_engin.yml": "device; machine; vehicle",
    "cards/4353_polémique.yml": "controversy; polemic",
    "cards/4389_substitution.yml": "substitution; replacement",
    "cards/4461_panier.yml": "basket",
    "cards/4497_génétiquement.yml": "genetically",
    "cards/4568_libéralisation.yml": "liberalization",
    "cards/4688_néfaste.yml": "harmful; detrimental",
    "cards/4736_vieillard.yml": "old man; elderly person",
    "cards/4760_licenciement.yml": "dismissal; layoff",
    "cards/4844_micro.yml": "microphone; micro-",
    "cards/4880_accélération.yml": "acceleration",
    "cards/4964_raser.yml": "to shave; skim; raze",
}

NAME_RESTORATIONS = {
    "Marie": "Mary",
    "Pierre": "Peter",
    "Jean": "John",
    "Jacques": "James",
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


def replace_de_note(text: str) -> str:
    old = '<p class="attention">The preposition <b>de</b> Mixed with the <a grammar="Der bestimmte Artikel">definite article</a> <b>le</b> or <b>les</b> In one word:'
    new = '<p class="attention">The preposition <b>de</b> combines with the <a grammar="Der bestimmte Artikel">definite article</a> <b>le</b> or <b>les</b> to form a single word:'
    return text.replace(old, new)


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
        elif current_fr is not None:
            indent = line[: len(line) - len(line.lstrip())]
            newline = "\n" if raw.endswith("\n") else ""
            value = EXAMPLES.get(current_fr, stripped)
            for french_name, english_name in NAME_RESTORATIONS.items():
                if re.search(rf"\b{re.escape(french_name)}\b", current_fr):
                    value = re.sub(rf"\b{re.escape(english_name)}\b", french_name, value)
            lines[i] = f"{indent}{value}{newline}"
        pair_pos += 1
    text = "".join(lines)
    if rel in DEFINITIONS:
        text = replace_definition(text, DEFINITIONS[rel])
    if rel == "cards/0002_de.yml":
        text = replace_de_note(text)
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
