#!/usr/bin/env python3
"""Expanded clean-source adaptations for an English-speaking French course.

This layers additional reviewed, path-scoped source rewrites on top of v1.  The
machine translator then sees English learner-specific explanations directly rather
than literal German-audience comparisons.  Every source fragment must match exactly
once, so changes in the clean baseline fail closed.
"""
from __future__ import annotations

from pathlib import Path

from adapt_grammar_clean_source_en import PATH_REPLACEMENTS as BASE_REPLACEMENTS

EXTRA_REPLACEMENTS: dict[str, list[tuple[str, str]]] = {
    "07 Pronomen/09 Die Demonstrativbegleiter.html": [
        (
            "Demonstrativbegleiter haben eine hinweisende Funktion: Sie bestimmen ein Substantiv näher. Im Deutschen gibt es zwei Demonstrativbegleiter: <span class=\"de\">diese(&#8209;r/s)</span> und <span class=\"de\">jene(&#8209;r/s)</span>. Das Französische hat nur einen, der sich in Geschlecht und Zahl dem begleiteten Substantiv anpasst.",
            "Demonstrative determiners point out or identify a noun. English distinguishes forms such as “this/that” and “these/those.” French uses one demonstrative-determiner paradigm that agrees with the noun in gender and number; distance can be clarified with <span class=\"fr\">&#8209;ci</span> and <span class=\"fr\">&#8209;là</span>.",
        ),
    ],
    "10 Zeitformen und Modi/01 Présent.html": [
        (
            "Das <b>présent</b> (Präsens) ist eine einfache Zeitform des Indikativs. Es beschreibt, ähnlich wie im Deutschen, gegenwärtige Ereignisse und Handlungen, die zum Sprechzeitpunkt stattfinden, sowie Gewohnheiten und allgemeine Tatsachen.",
            "The <b>présent</b> is a simple indicative tense. It covers actions happening now, habitual actions, and general facts; depending on context, English may use the simple present or the present progressive.",
        ),
    ],
    "10 Zeitformen und Modi/05 Plus-que-parfait.html": [
        (
            "Das <b>plus-que-parfait</b> (Plusquamperfekt) ist eine zusammengesetzte Vergangenheitsform des Indikativs. Es wird ähnlich wie im Deutschen verwendet, um ein Ereignis zu beschreiben, das vor einem anderen Ereignis in der Vergangenheit stattgefunden hat.",
            "The <b>plus-que-parfait</b> is a compound indicative past tense used for an event that occurred before another event in the past, much like the English past perfect.",
        ),
        (
            "In einigen Ausrufesätzen wird im Französischen das <i>plus-que-parfait</i> verwendet, während im Deutschen das Perfekt steht.",
            "In some exclamations French can use the <i>plus-que-parfait</i> where idiomatic English would normally use a different past-tense construction.",
        ),
    ],
    "10 Zeitformen und Modi/07 Futur proche.html": [
        (
            "Das <b>futur proche</b> (auch <i>futur composé</i> genannt) drückt die nahe Zukunft aus. Es hat keine direkte Entsprechung im Deutschen.",
            "The <b>futur proche</b> (also called <i>futur composé</i>) expresses a near, intended, or strongly expected future. It is often close to English “be going to” + verb.",
        ),
    ],
    "10 Zeitformen und Modi/12 Subjonctif.html": [
        (
            "Der <i>subjonctif</i> wird meist in Nebensätzen verwendet, die mit <span class=\"fr\">que</span> (dass) beginnen. Er sollte nicht mit dem deutschen Konjunktiv verwechselt werden, z.B. in der indirekten Rede.",
            "The <i>subjonctif</i> is most often used in subordinate clauses introduced by <span class=\"fr\">que</span>. It is triggered by specific grammatical and semantic contexts and is not simply equivalent to the English subjunctive or to reported-speech marking.",
        ),
    ],
    "11 Partizip/1 Participe présent.html": [
        (
            "Viele deutsche zusammengesetzte Substantive werden im Französischen mit einem Verbaladjektiv gebildet.",
            "French often uses a verbal adjective in noun phrases where English may use a participle or a compound modifier.",
        ),
    ],
    "13 Ergänzung des Verbs/01 Die Ergänzung des Verbs.html": [
        (
            "Französische Verben können, ähnlich wie deutsche, verschiedene Ergänzungen haben, zum Beispiel:",
            "Like English verbs, French verbs can take different kinds of complements, for example:",
        ),
        (
            "Darin, was angeschlossen werden kann, stimmen das französische und das deutsche Verb nicht immer überein. Diese Unterschiede müssen gelernt werden.",
            "A French verb and its English equivalent do not always take the same kind of complement or preposition. Learn the complement pattern together with the verb.",
        ),
    ],
    "13 Ergänzung des Verbs/02 Verben mit direktem Objekt.html": [
        (
            "Die Ergänzungen der Verben im Französischen und Deutschen sind nicht immer identisch. Diese Liste konzentriert sich auf die Fälle, die für Deutschsprachige „falsche Freunde“ sind: Während das französische Verb transitiv ist (also ein direktes Objekt hat), verlangt das deutsche Gegenstück eine Präposition (z. B. <i>warten <b>auf</b></i>).",
            "French and English verb complements do not always match. The verbs below take a direct object in French even though a common English equivalent often uses a preposition (for example, <i>wait <b>for</b></i>).",
        ),
    ],
    "13 Ergänzung des Verbs/03 Verben mit à.html": [
        (
            "Die deutsche Übersetzung ist dabei manchmal nicht intuitiv – statt einer direkten Entsprechung wie „an“ oder „zu“ wird im Deutschen oft eine andere Präposition (z. B. <i>auf, mit, über</i>), der Dativ oder gar keine Präposition verwendet. Diese Liste konzentriert sich auf diese Fälle, die für Deutschsprachige „falsche Freunde“ sind.",
            "The English equivalent often does not use a direct counterpart of <b>à</b>; depending on the verb, English may use a different preposition or no preposition at all. Learn the French verb together with its <b>à</b> complement pattern.",
        ),
    ],
    "13 Ergänzung des Verbs/04 Verben mit de.html": [
        (
            "Die deutsche Übersetzung ist dabei oft nicht intuitiv. Statt der direkten Entsprechung „von“ wird im Deutschen oft eine andere Präposition (z. B. <i>an, auf, über, mit</i>) verwendet oder das Verb ist transitiv (hat also gar keine Präposition). Diese Liste konzentriert sich auf diese Fälle.",
            "The English equivalent often does not use a direct counterpart of <b>de</b>; it may take another preposition or a direct object instead. Learn the French verb together with its <b>de</b> complement pattern.",
        ),
    ],
    "13 Ergänzung des Verbs/06 Verben mit pour.html": [
        (
            "Die deutsche Übersetzung ist dabei manchmal nicht intuitiv. Statt der direkten Entsprechung „für“ wird im Deutschen manchmal eine andere Präposition (z. B. <i>als, nach, auf, um</i>) verwendet. Diese Liste konzentriert sich auf diese Fälle.",
            "The English equivalent does not always use “for”; depending on the verb, English may use another preposition or construction. Learn the French <b>pour</b> pattern together with the verb.",
        ),
    ],
    "13 Ergänzung des Verbs/07 Verben mit contre.html": [
        (
            "Die deutsche Übersetzung ist dabei manchmal nicht intuitiv. Statt der direkten Entsprechung „gegen“ wird im Deutschen manchmal eine andere Präposition (z. B. <i>vor, auf</i>) verwendet. Diese Liste konzentriert sich auf diese Fälle.",
            "The English equivalent does not always use “against”; depending on the expression, English may use another preposition or construction. Learn the French <b>contre</b> pattern together with the expression.",
        ),
    ],
    "13 Ergänzung des Verbs/08 Verben mit sur.html": [
        (
            "Die deutsche Übersetzung ist dabei manchmal nicht intuitiv. Statt der direkten Entsprechung „auf“ oder „über“ wird im Deutschen manchmal eine andere Präposition (z. B. <i>in, mit, an, zu, vor, gegenüber</i>) verwendet. Diese Liste konzentriert sich auf diese Fälle.",
            "The English equivalent does not always use “on” or “about”; depending on the expression, English may use another preposition or a different construction. Learn the French <b>sur</b> pattern together with the expression.",
        ),
    ],
    "13 Ergänzung des Verbs/09 Verben mit en.html": [
        (
            "Die deutsche Übersetzung ist dabei manchmal nicht intuitiv. Statt der direkten Entsprechung „in“ wird im Deutschen manchmal eine andere Präposition (z. B. <i>an, aus</i>) verwendet. Diese Liste konzentriert sich auf diese Fälle.",
            "The English equivalent does not always use “in”; depending on the expression, English may use another preposition or construction. Learn the French <b>en</b> pattern together with the expression.",
        ),
    ],
    "15 Bedingungssätze/1 Bedingungssätze mit si.html": [
        (
            "Anders als im Deutschen steht der <b>si</b>&#8209;Satz nie im <i>conditionnel</i>, sondern nur der Hauptsatz!",
            "In a standard French <b>si</b>&#8209;clause, do not use the <i>conditionnel</i>; the conditional belongs in the main clause.",
        ),
    ],
    "19 Inversion/1 Inversion mit Pronomen.html": [
        (
            "Im Französischen und Deutschen steht normalerweise das Subjekt vor dem Verb, wie bei <span class=\"fr\">vous êtes</span> (ihr seid). Beide Sprachen kennen auch die Inversion, bei der Verb und Subjekt die Plätze tauschen: <span class=\"fr\">êtes-vous</span> (seid ihr). Im Deutschen wird die Inversion hauptsächlich in Fragen und Nebensätzen verwendet, im Französischen hat sie mehrere Funktionen.",
            "French normally places the subject before the verb, as in <span class=\"fr\">vous êtes</span> (“you are”). In inversion, the verb comes before the subject pronoun, as in <span class=\"fr\">êtes-vous</span> (“are you”). English also uses subject–verb inversion in some questions, but French inversion has its own rules and several additional uses.",
        ),
    ],
    "20 Indirekte Rede/1 Die indirekte Rede.html": [
        (
            "Die indirekte Rede dient dazu, Gesagtes, Gedanken oder Wünsche wiederzugeben, ohne sie wörtlich zu zitieren. Im Französischen steht dabei, anders als im Deutschen, kein Konjunktiv, sondern der <b>Indikativ</b> oder der <b><a grammar=\"Conditionnel\">Conditionnel</a></b>. Aussage- und Aufforderungssätze werden mit der Konjunktion <span class=\"fr\">que</span> (<span class=\"de\">dass</span>) eingeleitet, die nicht weggelassen werden darf.",
            "Indirect speech reports words, thoughts, or wishes without quoting them directly. French normally uses the <b>indicative</b> or, where required by sequence of tenses or meaning, the <b><a grammar=\"Conditionnel\">conditionnel</a></b>. Reported statements are introduced by <span class=\"fr\">que</span>, which unlike English “that” cannot simply be omitted.",
        ),
    ],
    "21 Informelle Sprache/3 Informelle Fragen.html": [
        (
            "Eine Aussage wird durch Anheben der Stimme am Satzende zur Frage – genau wie im Deutschen:",
            "A statement can become a question simply through rising intonation at the end, much as in conversational English:",
        ),
    ],
    "22 Zahlen und Zeitangaben/4 Datumsangaben.html": [
        (
            "Abweichend vom Deutschen wird im Französischen nur für den <b>ersten Tag</b> des Monats die Ordnungszahl <span class=\"fr\">premier</span> verwendet. Für alle folgenden Tage wird einfach die <a grammar=\"Zahlen\">Grundzahl</a> benutzt.",
            "In French, only the <b>first day</b> of the month uses the ordinal <span class=\"fr\">premier</span>. All later dates use <a grammar=\"Zahlen\">cardinal numbers</a>, unlike English dates, which are normally read with ordinals.",
        ),
        (
            "Das Datum wird immer mit dem <a grammar=\"Der bestimmte Artikel\">bestimmten Artikel</a> <span class=\"fr\">le</span> genannt, wenn im Deutschen eine Präposition wie „am“ stehen würde.",
            "When giving a date in French, use the <a grammar=\"Der bestimmte Artikel\">definite article</a> <span class=\"fr\">le</span>; English normally expresses the same idea with “on” when a preposition is needed.",
        ),
    ],
}


def merged_replacements() -> dict[str, list[tuple[str, str]]]:
    merged = {path: list(rules) for path, rules in BASE_REPLACEMENTS.items()}
    for path, rules in EXTRA_REPLACEMENTS.items():
        merged.setdefault(path, []).extend(rules)
    return merged


def apply_page(path: Path, rules: list[tuple[str, str]]) -> int:
    raw = path.read_text(encoding="utf-8")
    changed = 0
    for old, new in rules:
        count = raw.count(old)
        if count != 1:
            rel = str(path.relative_to("grammar"))
            raise RuntimeError(
                f"{rel}: expected exactly one reviewed source fragment, found {count}: {old[:100]!r}"
            )
        raw = raw.replace(old, new, 1)
        changed += 1
    path.write_text(raw, encoding="utf-8")
    return changed


def apply_all() -> int:
    rules_by_path = merged_replacements()
    total = 0
    for rel in sorted(rules_by_path):
        path = Path("grammar") / rel
        if not path.exists():
            raise RuntimeError(f"missing grammar page for reviewed source adaptation: {rel}")
        changed = apply_page(path, rules_by_path[rel])
        total += changed
        print(f"{rel}: English-learner source adaptations={changed}")
    print(
        f"ENGLISH-LEARNER CLEAN-SOURCE ADAPTATIONS V2: "
        f"pages={len(rules_by_path)} replacements={total}"
    )
    return total


def main() -> int:
    apply_all()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
