#!/usr/bin/env python3
"""Second reviewed grammar repair layer from full-candidate QA findings.

This file fixes explanatory prose and a few markup-sensitive examples that should not
be entrusted to bulk translation. Replacements are exact and preserve all existing
compatibility attributes, French source spans, and IPA spans.
"""
from __future__ import annotations

from pathlib import Path

REPLACEMENTS: dict[str, list[tuple[str, str]]] = {
    "02 Aussprache/6 Die Aussprache von plus.html": [
        ("<p>If: <span class=\"fr\">plus</span> has a positive significance (<span class=\"de\">more</span>), the <b>&#8209;s</b> usually pronounced.</p>",
         "<p>When <span class=\"fr\">plus</span> means <span class=\"de\">more</span>, the pronunciation of the final <b>&#8209;s</b> depends on the following sound and on the grammatical context.</p>"),
        ("<h3><i>Plus</i> as a denial (<span class=\"de\">She's smarter than her friend.</span>)</h3>",
         "<h3><i>Plus</i> in negation (<span class=\"de\">no longer, no more</span>)</h3>"),
        ("<p class=\"attention\">When <span class=\"fr\">plus</span> is part of a negative expression, its final <b>&#8209;s</b> is <b>not</b> pronounced <span class=\"ipa\">\\s\\</span>.</p>",
         "<p class=\"attention\">When <span class=\"fr\">plus</span> is part of a negative expression, its final <b>&#8209;s</b> is <b>not</b> pronounced \\s\\.</p>"),
        ("<li>before a word beginning with a <b>vowel</b> or <b>silent h</b>, liaison with <span class=\"ipa\">\\z\\</span> is possible. It is more common in careful or formal speech and is often omitted in everyday speech.</li>",
         "<li>before a word beginning with a <b>vowel</b> or <b>silent h</b>, liaison with \\z\\ is possible. It is more common in careful or formal speech and is often omitted in everyday speech.</li>"),
        ("<h4>The &#8209;s can be used as <span class=\"ipa\">\\z\\</span> (liaison) (<span class=\"ipa\">\\plyz\\</span>) ...</h4>",
         "<h4>The final &#8209;s can be pronounced <span class=\"ipa\">\\z\\</span> in liaison (<span class=\"ipa\">\\plyz\\</span>) ...</h4>"),
        ("<div class=\"de spoiler\">It's not a single cake <u>more</u> (<span class=\"ipa\">\\plyz ɛ̃\\</span> or <span class=\"ipa\">\\ply ɛ̃\\</span>)</div>",
         "<div class=\"de spoiler\">There isn't a single cake <u>left</u>. (<span class=\"ipa\">\\plyz ɛ̃\\</span> or <span class=\"ipa\">\\ply ɛ̃\\</span>)</div>"),
        ("<div class=\"de spoiler\">We're not friends <u>more</u>. (<span class=\"ipa\">\\plyz ami\\</span> or <span class=\"ipa\">\\ply ami\\</span>)</div>",
         "<div class=\"de spoiler\">We are <u>no longer</u> friends. (<span class=\"ipa\">\\plyz ami\\</span> or <span class=\"ipa\">\\ply ami\\</span>)</div>"),
        ("<div class=\"de spoiler\">Five <u>plus</u> Five is ten.</div>",
         "<div class=\"de spoiler\">Five <u>plus</u> five is ten.</div>"),
        ("<div class=\"de spoiler\">This experience is a real <u>Plus</u> in deinem Lebenslauf.</div>",
         "<div class=\"de spoiler\">This experience is a real <u>plus</u> on your résumé.</div>"),
    ],
    "05 Adjektive/4 Adjektive mit zwei männlichen Formen.html": [
        ("Adjectives with two male forms", "Adjectives with two masculine forms"),
    ],
    "06 Adverbien/1 Die Formen von Adverbien.html": [
        ("<p>The adverb is formed by the ending <b>&#8209;ment</b> to the <a grammar=\"Adjektive in der Femininform\"><b>Female form</b> of the adjective</a> added.</p>",
         "<p>The adverb is usually formed by adding <b>&#8209;ment</b> to the <a grammar=\"Adjektive in der Femininform\"><b>feminine form</b> of the adjective</a>.</p>"),
    ],
    "07 Pronomen/01 Die verbundenen Personalpronomen.html": [
        ("<p>In French there is no equivalent to the German personal pronoun <span class=\"de\">They're sisters.</span>because French only knows masculine and feminine forms. Instead, one uses <span class=\"fr\">il</span> or <span class=\"fr\">elle</span>, depending on whether they are male or female persons or things, for example:</p>",
         "<p>French has no neuter personal pronoun corresponding to English <span class=\"de\">it</span>. Use <span class=\"fr\">il</span> or <span class=\"fr\">elle</span> according to the grammatical gender of the noun being referred to, for example:</p>"),
        ("<p>While in German <span class=\"de\">It's interesting.</span> in the 3rd person plural is used for both sexes, the French distinguishes between <span class=\"fr\">ils</span> (male) and <span class=\"fr\">elles</span> (female), for example:</p>",
         "<p>French distinguishes <span class=\"fr\">ils</span> for masculine or mixed-gender groups from <span class=\"fr\">elles</span> for all-feminine groups, for example:</p>"),
        ("<h3>Die umgangssprachliche Verwendung von <span class=\"fr\">on</span></h3>",
         "<h3>Informal use of <span class=\"fr\">on</span></h3>"),
        ("<p>In der gesprochenen Sprache und im informellen Schriftverkehr wird <a grammar=\"Informelle Pronomen\"><span class=\"fr\">on</span> fast immer anstelle von <span class=\"fr\">nous</span> verwendet</a>, um <span class=\"de\">we</span> auszudrücken. Obwohl <span class=\"fr\">on</span> formal die 3. Person Singular ist, bezieht es sich in diesem Kontext auf die 1. Person Plural.</p>",
         "<p>In spoken French and informal writing, <a grammar=\"Informelle Pronomen\"><span class=\"fr\">on</span> is very often used instead of <span class=\"fr\">nous</span></a> to mean <span class=\"de\">we</span>. Although <span class=\"fr\">on</span> is grammatically third-person singular, in this use it refers to the first-person plural.</p>"),
        ("<h3>Die Höflichkeitsform <span class=\"fr\">vous</span></h3>",
         "<h3>Polite <span class=\"fr\">vous</span></h3>"),
        ("<p><span class=\"fr\">Vous</span> dient auch als Höflichkeitsform für eine oder mehrere Personen, unabhängig vom Geschlecht.</p>",
         "<p><span class=\"fr\">Vous</span> is also used as the polite form when addressing one or more people, regardless of gender.</p>"),
    ],
    "07 Pronomen/02 Die unverbundenen Personalpronomen.html": [
        ("The unconnected personnel pronouns", "Stressed personal pronouns"),
        ("<p>The unconnected personnel pronouns (<span class=\"fr\">pronoms personnels toniques</span>) are used to emphasize a subject. In German there is no direct correspondence for this form.</p>",
         "<p>Stressed personal pronouns (<span class=\"fr\">pronoms personnels toniques</span>) are used for emphasis and in positions where the unstressed subject or object pronouns cannot be used. English has no single directly corresponding form.</p>"),
    ],
    "07 Pronomen/06 Das Adverbialpronomen en.html": [
        ("<p>When <b>en</b> eine quantity expression, ein numeral or <b>un/une</b> + Substantiv vertritt, is die quantity expression, das numeral or der unbestimmte Artikel im nachfolgenden Satz wiederholt.</p>",
         "<p>When <b>en</b> replaces a quantity expression, a numeral, or <b>un/une</b> + noun, the quantity, numeral, or indefinite article is repeated after <b>en</b>.</p>"),
    ],
    "09 Verben/10 Unpersönliche Verben.html": [
        ("<div class=\"de spoiler\"><u>Daraus folgt</u>That we have to go.</div>",
         "<div class=\"de spoiler\"><u>It follows</u> that we have to leave.</div>"),
    ],
    "13 Ergänzung des Verbs/03 Verben mit à.html": [
        ("<p>Many verbs are used with preposition <b>à</b> connected to an object: you ask for the object with <i>Who?</i> (<span class=\"fr no-audio\">à qui ?</span>) or <i>woran/worauf?</i> (<span class=\"fr no-audio\">à quoi ?</span>)</p>",
         "<p>Many French verbs take a complement introduced by <b>à</b>. Ask <i>to whom?</i> (<span class=\"fr no-audio\">à qui ?</span>) for people or <i>to what?/what about?</i> (<span class=\"fr no-audio\">à quoi ?</span>) for things.</p>"),
        ("<p class=\"attention\">The German translation is sometimes not intuitive – instead of a direct equivalent such as \"on\" or \"on\" it often becomes a different preposition in German (e.g. <i>on, with, over</i>This list focuses on these cases, which are \"wrong friends\" for German-speaking people.</p>",
         "<p class=\"attention\">The English equivalent often uses a different construction or preposition, so it is best to learn each verb together with <b>à</b> and its complement pattern.</p>"),
        ("<div class=\"de spoiler\">The result <u>entspricht</u> not <u>the</u> Erwartungen.</div>",
         "<div class=\"de spoiler\">The result does not <u>match</u> <u>the</u> expectations.</div>"),
    ],
    "16 Präpositionen/1 Präpositionen des Ortes.html": [
        ("Prepositions of the place", "Prepositions of Place"),
        ("<p>The prepositions of the place provide information about the spatial relationship between objects or persons.</p>",
         "<p>Prepositions of place describe locations, origins, destinations, directions, and other spatial relationships.</p>"),
        ("<p>Is used to indicate general objectives or whereabouts:</p>", "<p>Used for general locations and destinations:</p>"),
        ("<span class=\"de\">of which:</span>", "<span class=\"de\">in; to</span>"),
        ("<span class=\"de\">with, to</span>", "<span class=\"de\">at; to the home or premises of</span>"),
        ("<p>Designates objectives or whereabouts of persons or undertakings:</p>", "<p>Used for a person's home or a professional/business premises:</p>"),
        ("<p>Wird für konkrete Ortsangaben verwendet, z.B. in Räumen:</p>", "<p>Used for specific locations, especially inside an area or space:</p>"),
        ("<p>Gibt die Herkunft oder den Ausgangspunkt an:</p>", "<p>Indicates origin or point of departure:</p>"),
        ("<p>Vor Vokal und <a grammar=\"Das h aspiré\">silent h</a> wird <span class=\"fr\">de</span> zu <span class=\"fr\">d'</span>.</p>",
         "<p>Before a vowel or <a grammar=\"Das h aspiré\">silent h</a>, <span class=\"fr\">de</span> becomes <span class=\"fr\">d'</span>.</p>"),
        ("<p>Bezeichnet das Durchqueren eines Raumes und wird oft mit Verben der Bewegung used:</p>", "<p>Indicates movement through or via a place and is often used with verbs of motion:</p>"),
        ("<p>Bezeichnet den Zielpunkt einer Reise, z.B. ein Land oder eine Stadt, oft mit den Verben <span class=\"fr\">partir</span> und <span class=\"fr\">s'embarquer</span>:</p>",
         "<p>Marks the destination of a journey, such as a country or city, especially with <span class=\"fr\">partir</span> and <span class=\"fr\">s'embarquer</span>:</p>"),
        ("<p>Bezeichnet das Ziel einer Bewegung, z.B. ein Land, eine Stadt, eine Himmelsrichtung oder eine Person:</p>", "<p>Indicates movement toward a place, direction, or person:</p>"),
        ("<h3>Weitere nützliche Präpositionen</h3>", "<h3>Other Useful Prepositions</h3>"),
        ("<span class=\"de\">Page</span>", "<span class=\"de\">next to; beside</span>"),
        ("<span class=\"de\">the right side; straight</span>", "<span class=\"de\">to the right of</span>"),
        ("<span class=\"de\">on the left</span>", "<span class=\"de\">to the left of</span>"),
        ("<span class=\"de\">The end, the top</span>", "<span class=\"de\">at the end of</span>"),
        ("<span class=\"de\">Floor, background</span>", "<span class=\"de\">at the back/bottom of</span>"),
        ("<span class=\"de\">Behind the</span>", "<span class=\"de\">behind</span>"),
        ("<span class=\"de\">before [literally]</span>", "<span class=\"de\">in front of</span>"),
        ("<span class=\"de\">Face; front</span>", "<span class=\"de\">opposite; across from</span>"),
        ("<span class=\"de\">Far and wide</span>", "<span class=\"de\">far from</span>"),
        ("<span class=\"de\">nearby</span>", "<span class=\"de\">near; close to</span>"),
    ],
    "16 Präpositionen/2 Präpositionen der Zeit.html": [
        ("Prepositions of time", "Prepositions of Time"),
        ("<p>The prepositions of time help to express temporal relationships and timings.</p>", "<p>Prepositions of time express points in time, duration, starting points, end points, and approximate times.</p>"),
        ("<div>Beachte: <span class=\"fr\"><u>au</u> printemps</span>, but <span class=\"fr\"><u>en</u> été, <u>en</u> automne, <u>en</u> hiver</span>.</div>",
         "<div>Note: <span class=\"fr\"><u>au</u> printemps</span>, but <span class=\"fr\"><u>en</u> été, <u>en</u> automne, <u>en</u> hiver</span>.</div>"),
        ("<span class=\"de\">Leave, take off</span>", "<span class=\"de\">starting from; as of</span>"),
        ("<span class=\"de\">before -her), before</span>", "<span class=\"de\">before</span>"),
        ("<span class=\"de\">of which:</span>", "<span class=\"de\">in; within</span>"),
        ("<p>Used before seasons starting with a vowel, months and years. <span class=\"fr\">en</span> a period during which an action takes place:</p>",
         "<p>Used with months, years, and most seasons. <span class=\"fr\">en</span> can also express the time taken to complete an action:</p>"),
        ("<div>For months, you can also <span class=\"fr\">au mois de</span> statt <span class=\"fr\">en</span> verwenden:</div>",
         "<div>With months, <span class=\"fr\">au mois de</span> can also be used instead of <span class=\"fr\">en</span>:</div>"),
        ("<span class=\"de\">there; to it</span>", "<span class=\"de\">ago</span>"),
        ("<div>After <span class=\"fr\">jusque</span> folgt oft <span class=\"fr\">à</span>, what to <span class=\"fr\">jusqu'à</span> The Commission's proposal is not in line with the Commission's proposal.</div>",
         "<div><span class=\"fr\">jusque</span> is often followed by <span class=\"fr\">à</span>, giving <span class=\"fr\">jusqu'à</span>.</div>"),
        ("<span class=\"de\">Whereas</span>", "<span class=\"de\">during; for</span>"),
    ],
    "16 Präpositionen/3 Modale Präpositionen.html": [
        ("Modal prepositions", "Prepositions of Manner and Means"),
        ("<p>Modal prepositions describe the way an event takes place and explain the circumstances of an action.</p>", "<p>These prepositions express purpose, means, manner, material, cause, price, and related circumstances.</p>"),
        ("<p>Press out:</p>", "<p>Common uses include:</p>"),
        ("<li>Zweck</li>", "<li>Purpose</li>"),
        ("<li>Preisangabe</li>", "<li>Price</li>"),
        ("<li>Fortbewegungsart</li>", "<li>Means of transport</li>"),
        ("<li>Entfernung</li>", "<li>Distance</li>"),
        ("<li>Materialangabe</li>", "<li>Material</li>"),
        ("<li>Ursache</li>", "<li>Cause</li>"),
        ("<p>Bezeichnet:</p>", "<p>Common uses include:</p>"),
        ("<li>Transport by means of transport</li>", "<li>Means of transport</li>"),
        ("<li>Mittel</li>", "<li>Means</li>"),
        ("<li>Urheberbezeichnung</li>", "<li>Agent or source</li>"),
        ("<li>Beweggrund</li>", "<li>Reason or motive</li>"),
        ("<li>Verteilung</li>", "<li>Distribution or rate</li>"),
        ("<span class=\"de\">of which:</span>", "<span class=\"de\">by; in; made of</span>"),
    ],
    "18 Verneinung/04 Verneinung ohne ne.html": [
        ("<p>For verbs, both parts of the negative adverb (<span class=\"fr\"><span class=\"tag-lemma\">ne</span> ... <span class=\"tag-lemma\">pas</span></span>) around the verb. For other word types, <span class=\"fr\">pas</span> but often without <span class=\"fr\">ne</span> is used.</p>",
         "<p>With verbs, the two parts of the negative expression (<span class=\"fr\"><span class=\"tag-lemma\">ne</span> ... <span class=\"tag-lemma\">pas</span></span>) normally surround the verb. With other parts of speech, <span class=\"fr\">pas</span> is often used without <span class=\"fr\">ne</span>.</p>"),
    ],
    "22 Zahlen und Zeitangaben/2 Ordnungszahlen.html": [
        ("<p>The order numbers are formed by the ending <b>&#8209;ième</b> to the corresponding cardinal number.</p>",
         "<p>Ordinal numbers are formed by adding <b>&#8209;ième</b> to the corresponding cardinal number.</p>"),
        ("<div class=\"de spoiler\">François Prime Minister</div>", "<div class=\"de spoiler\">Francis I</div>"),
    ],
    "22 Zahlen und Zeitangaben/4 Datumsangaben.html": [
        ("<div class=\"section-title\" data-topic=\"A1\">Datumsangaben</div>", "<div class=\"section-title\" data-topic=\"A1\">Dates</div>"),
        ("<p>By way of derogation from German, French is only used for the purposes of: <b>ersten Tag</b> of the month the number of orders <span class=\"fr\">premier</span> is used. For all following days, the <a grammar=\"Zahlen\">Grundzahl</a> is used.</p>",
         "<p>For dates, French uses <span class=\"fr\">premier</span> for the first day of a month. For all other days, use the <a grammar=\"Zahlen\">cardinal number</a>.</p>"),
        ("<p class=\"attention\">The date is always used with the <a grammar=\"Der bestimmte Artikel\">definite articles</a> <span class=\"fr\">le</span> In English, a preposition such as \"am\" would be called.</p>",
         "<p class=\"attention\">A French date normally uses the <a grammar=\"Der bestimmte Artikel\">definite article</a> <span class=\"fr\">le</span>; English usually expresses the same date without an equivalent article.</p>"),
    ],
    "99 Vokabeln/28 Falsche Freunde.html": [
        ("<span class=\"de\">Jump, set</span>", "<span class=\"de\">jump; leap; bound</span>"),
        ("<span class=\"de wrong left-x\">Jump, set</span> (Anleihe/Bindung)", "<span class=\"de wrong left-x\">bond</span> (financial bond / connection)"),
    ],
}


def main() -> int:
    changed_files = replacements = 0
    misses: list[str] = []
    for rel, pairs in REPLACEMENTS.items():
        path = Path("grammar") / rel
        if not path.exists():
            continue
        raw = path.read_text(encoding="utf-8")
        new = raw
        count = 0
        for old, replacement in pairs:
            if old in new:
                new = new.replace(old, replacement)
                count += 1
            else:
                misses.append(f"{rel}: {old[:90]}")
        if new != raw:
            path.write_text(new, encoding="utf-8")
            changed_files += 1
            replacements += count
            print(f"{rel}: reviewed-v3 replacements={count}")
    print(f"GRAMMAR REVIEWED PAGE REPAIRS V3: files={changed_files} replacements={replacements} misses={len(misses)}")
    for miss in misses:
        print(f"MISS {miss}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
