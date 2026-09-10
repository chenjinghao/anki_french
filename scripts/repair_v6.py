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
    for rel in paths:
        path = root / rel
        text = repair_text(path.read_text(encoding="utf-8"))
        if rel == "cards/1890_foutre.yml":
            text = replace_note_field(text, FOUTRE_NOTE)
        elif rel == "cards/5000_écrouler.yml":
            text = replace_note_field(text, ECROULER_NOTE)
        path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
