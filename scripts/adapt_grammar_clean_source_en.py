#!/usr/bin/env python3
"""Adapt German-audience grammar explanations for English-speaking learners.

This runs on the clean pre-merge German grammar *before* machine translation.  Each
replacement is exact and path-scoped, so reviewed language-specific pedagogy is not
left to NLLB and cannot drift between reruns.  French examples, IPA, attributes and
legacy target elements are not touched.
"""
from __future__ import annotations

from pathlib import Path

# Exact clean-source HTML fragments -> reviewed English learner-facing fragments.
# These are intentionally semantic adaptations, not mechanical Deutsch -> English
# substitutions; several contrasts differ between German and English.
PATH_REPLACEMENTS: dict[str, list[tuple[str, str]]] = {
    "01 Orthografie/1 Das Alphabet.html": [
        (
            "Das französische Alphabet hat 26 Buchstaben. Ihre Namen und ihre Aussprache unterscheiden sich teilweise vom Deutschen.",
            "The French alphabet has 26 letters. Several letter names and pronunciations differ from English.",
        ),
    ],
    "01 Orthografie/4 Groß- und Kleinschreibung.html": [
        (
            "Im Französischen wird grundsätzlich kleingeschrieben. Großschreibung wird seltener verwendet als im Deutschen. Vor allem Substantive, die keine Eigennamen sind, werden kleingeschrieben.",
            "French uses capitalization more sparingly than English. Common nouns are normally lowercase unless they begin a sentence, while proper names are capitalized.",
        ),
    ],
    "02 Aussprache/1 Die Aussprache.html": [
        (
            "Die folgende Übersicht zeigt französische Laute und Lautkombinationen, deren Aussprache sich deutlich vom Deutschen unterscheidet und daher besondere Aufmerksamkeit erfordert:",
            "The following overview highlights French sounds and letter combinations whose pronunciation differs notably from English and therefore deserves special attention:",
        ),
    ],
    "02 Aussprache/2 Die Aussprache der Vokale.html": [
        (
            "Die Aussprache der französischen Vokale weicht in vielen Fällen vom Deutschen ab. Besondere Aufmerksamkeit erfordern die Nasalvokale, die verschiedenen E-Laute und das stumme <i>e</i>.",
            "French vowel pronunciation differs from English in several important ways. Pay particular attention to nasal vowels, the different e sounds, and silent <i>e</i>.",
        ),
    ],
    "03 Artikel/1 Der bestimmte Artikel.html": [
        (
            "Im Französischen wird der bestimmte Artikel in einigen Fällen verwendet, in denen er im Deutschen nicht steht:",
            "French uses the definite article in several contexts where English normally does not:",
        ),
    ],
    "03 Artikel/2 Der unbestimmte Artikel.html": [
        (
            "Im Deutschen gibt es keinen unbestimmten Artikel im Plural. Im Französischen wird dafür <b>des</b> verwendet. Es entspricht dem deutschen Plural ohne Artikel oder auch „einige“.",
            "French has a plural indefinite article, <b>des</b>. In English it is often translated with no article or with “some”.",
        ),
    ],
    "05 Adjektive/1 Die Stellung des Adjektivs.html": [
        (
            "Anders als im Deutschen stehen die meisten Adjektive im Französischen <b>hinter</b> dem Substantiv, das sie beschreiben.",
            "Unlike English, most French adjectives come <b>after</b> the noun they describe.",
        ),
    ],
    "05 Adjektive/2 Adjektive im Plural.html": [
        (
            "Eine wichtige Besonderheit im Vergleich zum Deutschen: Auch prädikativ verwendete Adjektive (also nach <a grammar=\"Verben\">Verben</a> wie <span class=\"fr\">être</span>) werden an das Substantiv angepasst.",
            "A key difference from English is that predicative adjectives (for example after <a grammar=\"Verben\">verbs</a> such as <span class=\"fr\">être</span>) still agree with the noun in gender and number.",
        ),
    ],
    "05 Adjektive/5 Die Steigerung der Adjektive.html": [
        (
            "Der französische Komparativ der Unterlegenheit mit <span class=\"fr\">moins</span> wird im Deutschen üblicherweise durch den Komparativ des entgegengesetzten Adjektivs ausgedrückt, zum Beispiel:",
            "French commonly expresses inferiority with <span class=\"fr\">moins</span> + adjective. English can often express the same idea either with “less” + adjective or with the comparative of an opposite adjective, for example:",
        ),
    ],
    "07 Pronomen/11 Die Possessivbegleiter.html": [
        (
            "Anders als im Deutschen richtet sich der französische Possessivbegleiter nicht nach dem Geschlecht des Besitzers, sondern nach der Zahl und dem Geschlecht der besessenen Sache!",
            "Unlike English possessives such as “his” and “her,” French possessive determiners agree with the possessed noun in gender and number, not with the gender of the possessor.",
        ),
    ],
    "08 Fragen/1 Die drei Frageformen.html": [
        (
            "Das Deutsche kennt die Intonationsfrage nicht. Im gesprochenen Französisch wird sie jedoch häufig verwendet und ist sehr einfach zu bilden.",
            "In spoken French, yes/no questions are often formed simply with rising intonation while keeping statement word order, much as in conversational English.",
        ),
        (
            "Die Frage mit <span class=\"fr\">est-ce que</span> wird gebildet, indem man <span class=\"fr\">est-ce que</span> vor den Aussagesatz setzt. Die Stellung der einzelnen Satzglieder im Aussagesatz bleibt dabei unverändert. Die Frage mit <span class=\"fr\">est-ce que</span> existiert im Deutschen nicht. Sie wird sowohl in der gesprochenen als auch in der geschriebenen Sprache verwendet.",
            "An <span class=\"fr\">est-ce que</span> question is formed by placing <span class=\"fr\">est-ce que</span> before a statement; the statement word order otherwise stays unchanged. English has no direct equivalent of this fixed question marker. It is used in both spoken and written French.",
        ),
        (
            "Die Inversionsfrage ist dem Deutschen recht ähnlich. Sie wird allerdings im gesprochenen Französisch nicht sehr häufig verwendet. Man trifft sie hauptsächlich in schriftlich fixierten Texten an, z.B. in Briefen.",
            "French inversion puts the verb before the subject pronoun. It is relatively formal and is less common in everyday spoken French, though it remains common in formal questions and writing.",
        ),
    ],
    "08 Fragen/2 Die Fragepronomen.html": [
        (
            "Im Gegensatz zum Deutschen kann das Fragepronomen in der französischen Umgangssprache auch nachgestellt werden:",
            "In conversational French, a question word can also appear at the end of the sentence, a pattern that is much less common in standard English:",
        ),
    ],
    "08 Fragen/4 Fragen mit que.html": [
        (
            "Kurze Fragen mit <span class=\"fr tag-lemma rounded-border\">que</span> kann man wie im Deutschen bilden:",
            "Short formal questions can begin directly with <span class=\"fr tag-lemma rounded-border\">que</span>, followed by inversion:",
        ),
    ],
    "09 Verben/09 Reflexive Verben.html": [
        (
            "Reflexiv im Französischen vs. nicht reflexiv im Deutschen",
            "Reflexive in French vs. usually non-reflexive in English",
        ),
        (
            "Viele Verben sind im Französischen reflexiv, im Deutschen aber nicht.",
            "Many French verbs are reflexive even though their usual English equivalents are not.",
        ),
        (
            "Nicht reflexiv im Französischen vs. reflexiv im Deutschen",
            "Non-reflexive in French vs. different English constructions",
        ),
        (
            "Umgekehrt gibt es Verben, die im Deutschen reflexiv sind, im Französischen aber nicht.",
            "Conversely, some French verbs are non-reflexive where English may use a different construction. Learn the French verb pattern itself rather than transferring reflexivity from English.",
        ),
    ],
    "09 Verben/11 Der Infinitiv.html": [
        (
            "Der Infinitiv ist die Grundform des Verbs. Er wird nicht konjugiert, zeigt also weder Person noch Numerus an. Im Französischen wird der Infinitiv sehr vielseitig und häufiger als im Deutschen eingesetzt, oft als Substantiv oder in seiner reinen Verb-Funktion.",
            "The infinitive is the basic, unconjugated verb form and therefore marks neither person nor number. French uses infinitives very flexibly, including in places where English may use an infinitive, a gerund, or another construction.",
        ),
    ],
}


def apply_page(path: Path) -> int:
    rel = str(path.relative_to("grammar"))
    rules = PATH_REPLACEMENTS.get(rel)
    if not rules:
        return 0
    raw = path.read_text(encoding="utf-8")
    changed = 0
    for old, new in rules:
        count = raw.count(old)
        if count != 1:
            raise RuntimeError(f"{rel}: expected exactly one reviewed source fragment, found {count}: {old[:100]!r}")
        raw = raw.replace(old, new, 1)
        changed += 1
    path.write_text(raw, encoding="utf-8")
    print(f"{rel}: English-learner source adaptations={changed}")
    return changed


def apply_all() -> int:
    total = 0
    for rel in sorted(PATH_REPLACEMENTS):
        path = Path("grammar") / rel
        if not path.exists():
            raise RuntimeError(f"missing grammar page for reviewed source adaptation: {rel}")
        total += apply_page(path)
    print(f"ENGLISH-LEARNER CLEAN-SOURCE ADAPTATIONS: pages={len(PATH_REPLACEMENTS)} replacements={total}")
    return total


def main() -> int:
    apply_all()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
