#!/usr/bin/env python3
"""Deterministic cleanup for NLLB v6 pilot output.

This layer handles known French-learning terminology, semantic regressions, and
multiline notes that are poorly served by fragment-level MT. It intentionally
preserves compatibility-sensitive field names, HTML tags, classes and French text.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path


FOUTRE_NOTE = """Notiz: >-
  <b>foutre</b> is a vulgar and colloquial verb whose meaning depends heavily on context.
  In general it describes an action in a crude, impolite, or extremely casual way. It can
  mean things such as “do”, “put”, “give”, or “fuck”. It is also commonly used as an
  expletive to express anger, frustration, or indifference, as in <i>je m'en fous</i>
  (“I don't give a damn / I don't care”). In sexual contexts, <b>foutre</b> can mean
  “to fuck” and is therefore considered vulgar French.
"""

AIMER_NOTE = """Notiz: |-
  <div class="section">
    <div class="section-title"><i>aimer</i> vs <i>aimer bien/beaucoup</i></div>
    <div class="section-content">
      <p>In French, <span class="fr">aimer</span> on its own and with modifiers such as <span class="fr">bien</span> or <span class="fr">beaucoup</span> can have surprisingly different degrees of intensity.</p>

      <p><span class="fr">Aimer</span> without a modifier expresses strong, deep affection — often romantic love or very strong feelings. So <span class="fr">"Je t'aime"</span> means <span class="de">"I love you"</span> in the full sense of the word.</p>

      <div class="examples">
        <div class="fr">Je t'aime.</div>
        <div class="de spoiler">I love you.</div>
        <div class="fr">J'aime mes enfants plus que tout.</div>
        <div class="de spoiler">I love my children more than anything.</div>
      </div>

      <p>Paradoxically, adding <span class="fr">bien</span> or <span class="fr">beaucoup</span> can weaken the statement. <span class="fr">Aimer bien</span> usually means <span class="de">"to like"</span> or <span class="de">"to be fond of"</span>, while <span class="fr">aimer beaucoup</span> means <span class="de">"to like very much"</span> — still without necessarily expressing romantic love.</p>

      <div class="examples">
        <div class="fr">Je t'aime bien, mais seulement comme ami.</div>
        <div class="de spoiler">I like you, but only as a friend.</div>
        <div class="fr">J'aime beaucoup le chocolat.</div>
        <div class="de spoiler">I like chocolate very much.</div>
        <div class="fr">Elle aime bien son nouveau collègue.</div>
        <div class="de spoiler">She likes her new colleague.</div>
      </div>

      <p>This distinction is especially important with people: <span class="fr">"Je t'aime"</span> is a declaration of love, whereas <span class="fr">"Je t'aime bien"</span> expresses friendly affection and can even be understood as a gentle rejection of romantic feelings.</p>
    </div>
  </div>
  <!-- Grammar automatically added -->
  <grammar data-id="Modal- und Hilfsverben"></grammar>
  <grammar data-id="Der Infinitiv ohne Präposition"></grammar>
"""

REGARDER_NOTE = """Notiz: |-
  <div><span class="fr">Regarder</span> means <span class="de">to look at / watch</span>: to direct your gaze deliberately at something or observe it for a period of time. The verb describes an active act of looking.</div>
  <div class="examples">
    <div class="fr">Madame Rose <span class="fr">regarde</span> le coucher de soleil.</div>
    <div class="de spoiler">Mrs. Rose is watching the sunset.</div>
  </div>
  <div>Use <span class="fr">regarder</span> in the imperative to draw someone's attention to something.</div>
  <div class="examples">
    <div class="fr">Regarde ! Le chat est monté tout en haut de l'arbre!</div>
    <div class="de spoiler">Look! The cat climbed all the way to the top of the tree! (<span class="de">not:</span> Vois! Le chat...)</div>
  </div>
  <div class="attention">For the expression <span class="de">to watch a film/program</span>, French normally uses <span class="fr">regarder</span> in the present and future, but <span class="fr">voir</span> is common when referring to having seen a film in the past.</div>
  <div class="examples">
    <div class="fr">Ce soir, je vais rester à la maison et regarder un film à la télévision.</div>
    <div class="de spoiler">Tonight I'm staying home and watching a film on TV.</div>
    <div class="fr">Hier, j'ai <span class="fr">vu</span> un très bon film.</div>
    <div class="de spoiler">Yesterday I saw a very good film.</div>
  </div>
  <!-- Grammar automatically added -->
  <hr>
  <grammar data-id="Verben mit direktem Objekt"></grammar>
  <grammar data-id="Der Infinitiv ohne Präposition"></grammar>
"""

TENANT_NOTE = """Notiz: |-
  <p>The French word <span class="fr">tenant</span> has several meanings that developed from the basic idea of <i>holding</i>. It can refer to a supporter or advocate who “holds” a particular position. In sports, a <span class="fr">tenant</span> or <span class="fr">tenante</span> can be the defending champion or title holder. The expression <i>les tenants et les aboutissants</i> means the ins and outs, background, or full circumstances of a matter. Finally, <i>d’un seul tenant</i> means “in one continuous piece” or “contiguous”.</p>
"""

ECROULER_NOTE = """Notiz: |-
  <div class="celebration">
    <p><b>🏁 GOAL REACHED: 5,000 WORDS!</b></p>
    <p>Congratulations, you have completed the entire deck! This is the result of remarkable discipline and perseverance. Your comprehension and ability to express yourself are now at a very high level (B2/C1), something you can be proud of.</p>
    <p>The language is yours now. Play with it and discover its beauty in literature, film, and music. Your toolbox is full — now it is time to get creative.</p>
    <p>Tell the <a href="https://github.com/jacbz/anki_french/discussions/70">community</a> about your achievement and share your final statistics from the <a href="https://ankiweb.net/shared/info/637361797">add-on</a> — you earned it!</p>
  </div>
  <hr>
  <div class="section">
    <div class="section-title"><i>effondrer</i> and <i>écrouler</i></div>
    <div class="section-content">
      <p><span class="fr">S'effondrer</span> means <span class="de">"to collapse"</span> or <span class="de">"to cave in"</span> and can be used for both physical structures and abstract concepts. It often implies a sudden or dramatic collapse.</p>
      <div class="examples">
        <div class="fr">Le toit s'est effondré sous le poids de la neige.</div>
        <div class="de spoiler">The roof collapsed under the weight of the snow.</div>
        <div class="fr">L'économie du pays s'est effondrée en quelques mois.</div>
        <div class="de spoiler">The country's economy collapsed within a few months.</div>
        <div class="fr">Elle s'est effondrée en larmes en apprenant la nouvelle.</div>
        <div class="de spoiler">She burst into tears when she heard the news.</div>
      </div>
      <p><span class="fr">S'écrouler</span> likewise means <span class="de">"to collapse"</span> or <span class="de">"to fall down"</span>, but it is used mainly for physical structures and places more emphasis on the act of falling.</p>
      <div class="examples">
        <div class="fr">Le vieux mur s'est écroulé pendant la tempête.</div>
        <div class="de spoiler">The old wall collapsed during the storm.</div>
        <div class="fr">Il s'est écroulé de fatigue après sa longue journée de travail.</div>
        <div class="de spoiler">He collapsed from exhaustion after his long day at work.</div>
      </div>
      <p>Both verbs describe a collapse, but <span class="fr">s'effondrer</span> has a broader range of uses and is more common for abstract concepts, whereas <span class="fr">s'écrouler</span> is traditionally used more for concrete, physical collapses.</p>
    </div>
  </div>
  <!-- Grammar automatically added -->
  <grammar data-id="Reflexive Verben"></grammar>
"""

TEXT_REPLACEMENTS = {
    "Führerin": "guide",
    "Führer": "guide",
    "Marie has always been a mathematician.": "Marie has always been *talented* at mathematics.",
    "His linguistic versatility impresses everyone.": "His linguistic fluency impresses everyone.",
    "His linguistic dexterity impresses everyone.": "His linguistic fluency impresses everyone.",
    "I don't recognize this place.": "Where am I? I don't recognize this place.",
    "She *missed* him by ear.": "She *slapped* him across the face.",
    "She missed him by ear.": "She slapped him across the face.",
    "You did it by all means.": "They succeeded by every possible means.",
    "The window goes *to the sea*.": "The window *faces the sea*.",
    "The window goes to the sea.": "The window faces the sea.",
    '"*How to see yourself again*!"': '"*Fancy meeting you here*!"',
    '"How to see yourself again!"': '"Fancy meeting you here!"',
    "Did you find my keys again?": "Did you *find* my keys? I've been looking everywhere for them!",
    "She's been getting used to smoking for three months.": "She has been *out of the habit of smoking* for three months.",
    "We've received thousands upon thousands of requests.": "We've received *millions and millions* of requests.",
    "This million euro will be used to renovate the school.": "This *one million euros* will be used to renovate the school.",
    "The cat was gradually purified in a very short time.": "The cat became *house-trained* very quickly.",
    "You have conducted a clean matter without any scandal.": "They conducted a *clean operation* without any scandal.",
    "We don't keep this article in business all the time.": "We don't *stock* this item in the store.",
    "They insist *too much* on details and neglect the essentials.": "You focus *too much* on details and neglect the essentials.",
    "Then they reconciled.": "After that, they reconciled.",
    "The guard set up a guard at the door.": "The guard *posted* a sentry at the door.",
    "She never speaks at family meetings.": "She never manages to *get a word in* during family meetings.",
    "The player *placed* his shot perfectly into the left corner of the gate.": "The player *placed* his shot perfectly in the left corner of the goal.",
    "The author moved the story to the 1920s.": "The author *set* the story in the 1920s.",
    "I forgot how to make a cake.": "I forgot how to make a tart.",
    "They found him dead, drowned in the bathroom.": "They found him dead, *slumped* in the bathroom.",
    "The big oak has *collapsed* on the street.": "The large oak *fell* across the road.",
    "The government has been overthrown after a vote of no confidence.": "The government *collapsed* after a vote of no confidence.",
    "The business offers convenient payment facilities.": "The store offers attractive *payment options*.",
    "School offers all the possibilities for success.": "The school provides all the *facilities* needed for success.",
    "The preposition de Mixed with the definite article le or les In one word:":
        "The preposition de combines with the definite articles le and les to form a single word:",
    "The preposition de mixes with the definite article le or les in one word:":
        "The preposition de combines with the definite articles le and les to form a single word:",
    "is addressed in French to the": "agrees in French with the",
    "des Substantivs.": "of the noun.",
    "In French, there is no distinction between der, die and das.":
        "In French, the relative pronoun does not distinguish grammatical gender.",
    "In French, there is no distinction between “der”, “die” and “das”.":
        "In French, the relative pronoun does not distinguish grammatical gender.",
}

DE_SPAN_REPLACEMENTS = {
    "essen": "to eat",
    "sprechen": "to speak",
    "sein": "to be",
    "scheinen": "to seem",
    "regnen": "to rain",
    "ankommen": "to arrive",
    "spielen": "to play",
    "beenden": "to finish",
    "schlafen": "to sleep",
    "verlieren": "to lose",
    "bekommen": "to receive",
}


def replace_note_field(text: str, replacement: str) -> str:
    lines = text.splitlines(keepends=True)
    start = next((i for i, line in enumerate(lines) if line.startswith("Notiz:")), None)
    if start is None:
        return text
    end = start + 1
    while end < len(lines):
        line = lines[end]
        if line and not line.startswith((" ", "\t")):
            break
        end += 1
    new_lines = replacement.splitlines(keepends=True)
    if new_lines and not new_lines[-1].endswith("\n"):
        new_lines[-1] += "\n"
    return "".join(lines[:start] + new_lines + lines[end:])


def repair_text(text: str) -> str:
    for old, new in TEXT_REPLACEMENTS.items():
        text = text.replace(old, new)
    for old, new in DE_SPAN_REPLACEMENTS.items():
        pattern = re.compile(
            rf'(<span\b[^>]*class=["\'][^"\']*\bde\b[^"\']*["\'][^>]*>)\s*{re.escape(old)}\s*(</span>)',
            re.I,
        )
        text = pattern.sub(lambda m, value=new: m.group(1) + value + m.group(2), text)
    text = re.sub(
        r"We(?:'|’)re looking for all sorts of relief for our (?:clients|customers)\.",
        "We are looking for every possible convenience for our customers.",
        text,
        flags=re.I,
    )
    return text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--paths-file", required=True)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    paths = [
        line.strip()
        for line in Path(args.paths_file).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    note_replacements = {
        "cards/0242_aimer.yml": AIMER_NOTE,
        "cards/0425_regarder.yml": REGARDER_NOTE,
        "cards/1890_foutre.yml": FOUTRE_NOTE,
        "cards/2516_tenant.yml": TENANT_NOTE,
        "cards/5000_écrouler.yml": ECROULER_NOTE,
    }
    for rel in paths:
        path = root / rel
        text = repair_text(path.read_text(encoding="utf-8"))
        if rel in note_replacements:
            text = replace_note_field(text, note_replacements[rel])
        path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
