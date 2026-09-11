#!/usr/bin/env python3
"""Reviewed page-level grammar repairs for malformed mixed German/English prose.

These are exact, auditable replacements on known pages. They deliberately preserve
French source spans, IPA spans, compatibility classes/IDs and grammar link targets.
The generic safe repair pass handles terminology; this file handles sentences whose
meaning or syntax was damaged by the original machine translation.
"""
from __future__ import annotations

from pathlib import Path

REPLACEMENTS: dict[str, list[tuple[str, str]]] = {
    "02 Aussprache/5 Die Liaison.html": [
        ("<li><b>pronouns + pronomen</b>", "<li><b>Pronoun + pronoun</b>"),
        ("<h3>Binding liaisons (<i>Liaisons obligatoires</i>)</h3>", "<h3>Mandatory liaisons (<i>liaisons obligatoires</i>)</h3>"),
        ("<p>Liaison shall be binding in the following cases:</p>", "<p>Liaison is normally required in the following cases:</p>"),
    ],
    "02 Aussprache/6 Die Aussprache von plus.html": [
        ("<div class=\"section-title\" data-topic=\"B1\">The debate on: <i>plus</i></div>", "<div class=\"section-title\" data-topic=\"B1\">Pronunciation of <i>plus</i></div>"),
        ("<p>The debate on: <span class=\"fr tag-lemma rounded-border\">plus</span> There are three variations depending on the meaning and context: <span class=\"ipa\">\\plys\\</span>, <span class=\"ipa\">\\ply\\</span> and <span class=\"ipa\">\\plyz\\</span>.</p>", "<p><span class=\"fr tag-lemma rounded-border\">plus</span> has three common pronunciations depending on meaning and context: <span class=\"ipa\">\\plys\\</span>, <span class=\"ipa\">\\ply\\</span> and <span class=\"ipa\">\\plyz\\</span>.</p>"),
        ("<h3><i>Plus</i> as a comparative word (<span class=\"de\">more</span>)</h3>", "<h3><i>Plus</i> meaning <span class=\"de\">more</span></h3>"),
        ("<p>If: <span class=\"fr\">plus</span> has a positive significance (<span class=\"de\">more, additional</span>), the <b>&#8209;s</b> usually pronounced.</p>", "<p>When <span class=\"fr\">plus</span> has a positive meaning such as <span class=\"de\">more, additional</span>, the final <b>&#8209;s</b> may be pronounced according to the following rules.</p>"),
        ("<h4>The &#8209;s is used as <span class=\"ipa\">\\s\\</span> ausgesprochen (<span class=\"ipa\">\\plys\\</span>) ...</h4>", "<h4>The final &#8209;s is pronounced <span class=\"ipa\">\\s\\</span> (<span class=\"ipa\">\\plys\\</span>) ...</h4>"),
        ("<li>If: <span class=\"fr\">plus</span> a verb describes:</li>", "<li>when <span class=\"fr\">plus</span> modifies a verb:</li>"),
        ("<li>If: <span class=\"fr\">plus de</span> in front of a noun:</li>", "<li>with <span class=\"fr\">plus de</span> before a noun:</li>"),
        ("<li>If: <span class=\"fr\">plus</span> at the end of a sentence or in fixed expressions:</li>", "<li>when <span class=\"fr\">plus</span> occurs at the end of a sentence or in certain fixed expressions:</li>"),
        ("<h4>The &#8209;s will <u>not</u> ausgesprochen (<span class=\"ipa\">\\ply\\</span>) ...</h4>", "<h4>The final &#8209;s is <u>not</u> pronounced (<span class=\"ipa\">\\ply\\</span>) ...</h4>"),
        ("<li>If: <span class=\"fr\">plus</span> before a <a grammar=\"Adjektive\">Adjective</a> or <a grammar=\"Adverbien\">Adverb</a> The European Commission, DG XXIII, has published a report on the <b>Konsonanten</b> or a <b>h aspiré</b> beginnt:</li>", "<li>when <span class=\"fr\">plus</span> comes before an <a grammar=\"Adjektive\">adjective</a> or <a grammar=\"Adverbien\">adverb</a> beginning with a <b>consonant</b> or <b>h aspiré</b>:</li>"),
        ("<li>If: <span class=\"fr\">plus de</span> before a quantity indication (number):</li>", "<li>with <span class=\"fr\">plus de</span> before a numerical quantity:</li>"),
        ("<h4>The &#8209;s is used as <span class=\"ipa\">\\z\\</span> ausgesprochen (<a grammar=\"Die Liaison\">Liaison</a>) (<span class=\"ipa\">\\plyz\\</span>) ...</h4>", "<h4>The final &#8209;s is pronounced <span class=\"ipa\">\\z\\</span> in <a grammar=\"Die Liaison\">liaison</a> (<span class=\"ipa\">\\plyz\\</span>) ...</h4>"),
        ("<li>If: <span class=\"fr\">plus</span> an adjective or adverb with an <b>Vokal</b> or a <b>silent h</b> beginnt:</li>", "<li>when <span class=\"fr\">plus</span> comes before an adjective or adverb beginning with a <b>vowel</b> or <b>silent h</b>:</li>"),
        ("<h3><i>Plus</i> as a denial (<span class=\"de\">\"not anymore,\" \"no more.\"</span>)</h3>", "<h3><i>Plus</i> in negation (<span class=\"de\">no longer, no more</span>)</h3>"),
        ("<p class=\"attention\">If: <span class=\"fr\">plus</span> The Commission's proposal for a directive on the approximation of the laws of the Member States relating to <b>&#8209;s</b> am Ende <b>not</b> when \\s\\ pronounced!</p>", "<p class=\"attention\">When <span class=\"fr\">plus</span> is part of a negative expression, its final <b>&#8209;s</b> is <b>not</b> pronounced <span class=\"ipa\">\\s\\</span>.</p>"),
        ("<h4>The &#8209;s will <b>not</b> ausgesprochen (<span class=\"ipa\">\\ply\\</span>) ...</h4>", "<h4>The final &#8209;s is <b>not</b> pronounced (<span class=\"ipa\">\\ply\\</span>) ...</h4>"),
        ("<li>In most cases, e.g. at the end of the sentence or before a word, which has a <b>Konsonanten</b> or a <b>behauchten h</b> beginnt:</li>", "<li>in most cases, including at the end of a sentence and before a word beginning with a <b>consonant</b> or <b>h aspiré</b>:</li>"),
        ("<li>If the following word is used with a <b>Vokal</b> or a <b>silent h</b> This liaison is common in the upscale language, it is often omitted in everyday life.</li>", "<li>before a word beginning with a <b>vowel</b> or <b>silent h</b>, liaison with <span class=\"ipa\">\\z\\</span> is possible. It is more common in careful or formal speech and is often omitted in everyday speech.</li>"),
        ("<p>If: <span class=\"fr\">plus</span> (the plus) or as the arithmetic sign (+), the <b>&#8209;s</b> always as <span class=\"ipa\">\\s\\</span> pronounced.</p>", "<p>When <span class=\"fr\">plus</span> is a noun meaning “a plus/advantage” or the arithmetic sign (+), the final <b>&#8209;s</b> is pronounced <span class=\"ipa\">\\s\\</span>.</p>"),
    ],
    "03 Artikel/2 Der unbestimmte Artikel.html": [
        ("<p class=\"highlight\">In German there is no indefinite article in the plural. In French, for this there is no indeterminate article in the plural. <b>des</b> In English it is often translated with no article or with “some”.</p>", "<p class=\"highlight\">French uses <b>des</b> as a plural indefinite article. In English it is often translated with no article or with “some”.</p>"),
    ],
    "06 Adverbien/1 Die Formen von Adverbien.html": [
        ("<p>In adjectives that end in an audible vowel (but not on <b>&#8209;e</b>), <b>&#8209;ment</b> to the <b>Male form</b> Attached.</p>", "<p>For adjectives ending in a pronounced vowel other than <b>&#8209;e</b>, add <b>&#8209;ment</b> directly to the <b>masculine form</b>.</p>"),
    ],
    "07 Pronomen/01 Die verbundenen Personalpronomen.html": [
        ("<p>In der gesprochenen Sprache und im informellen Schriftverkehr wird <a grammar=\"Informelle Pronomen\"><span class=\"fr\">on</span> fast immer anstelle von <span class=\"fr\">nous</span> verwendet</a>, um <span class=\"de\">wir</span> auszudrücken. Obwohl <span class=\"fr\">on</span> formal die 3. Person Singular ist, bezieht es sich in diesem Kontext auf die 1. Person Plural.</p>", "<p>In spoken French and informal writing, <a grammar=\"Informelle Pronomen\"><span class=\"fr\">on</span> is very often used instead of <span class=\"fr\">nous</span></a> to mean <span class=\"de\">we</span>. Although <span class=\"fr\">on</span> is grammatically third-person singular, in this use it refers to the first-person plural.</p>"),
    ],
    "07 Pronomen/06 Das Adverbialpronomen en.html": [
        ("<li>the <a grammar=\"Der Teilungsartikel\">Teilungsartikel</a> + noun:</li>", "<li>the <a grammar=\"Der Teilungsartikel\">partitive article</a> + noun:</li>"),
        ("<p>When <b>en</b> eine quantity expression, ein numeral or <b>un/une</b> + Substantiv vertritt, is die quantity expression, das numeral or der unbestimmte Artikel im nachfolgenthe Satz wiederholt.</p>", "<p>When <b>en</b> replaces a quantity expression, a numeral, or <b>un/une</b> + noun, the quantity, numeral, or indefinite article is repeated after <b>en</b>.</p>"),
        ("<p>Das pronouns <b>en</b> replaces complements with <b>de</b> + inanimate nouns, z.B. nach the Verben <b>parler de</b>, <b>rêver de</b>, <b>revenir de</b>, <b>se souvenir de</b>, <b>rentrer de</b> etc.:</p>", "<p>The pronoun <b>en</b> also replaces complements introduced by <b>de</b> when they refer to things or places, for example after <b>parler de</b>, <b>rêver de</b>, <b>revenir de</b>, <b>se souvenir de</b>, and <b>rentrer de</b>:</p>"),
        ("<p>Das pronouns <b>en</b> comes before the conjugated verb. With a <a grammar=\"Verneinung\">negation</a> the negative expression surrounds <b>en</b> and the conjugated verb. In the <i><a grammar=\"Passé composé\">passé composé</a></i> or <i><a grammar=\"Plus-que-parfait\">plus-que-parfait</a></i> comes <b>en</b> before the conjugated <a grammar=\"Modal- und Hilfsverben\">auxiliary verb</a>.</p>", "<p>The pronoun <b>en</b> comes before the conjugated verb. With a <a grammar=\"Verneinung\">negation</a>, the negative expression surrounds <b>en</b> and the conjugated verb. In the <i><a grammar=\"Passé composé\">passé composé</a></i> and <i><a grammar=\"Plus-que-parfait\">plus-que-parfait</a></i>, <b>en</b> comes before the conjugated <a grammar=\"Modal- und Hilfsverben\">auxiliary verb</a>.</p>"),
        ("<p>Bei <a grammar=\"Impératif\">imperatives</a> is <b>en</b> attached to an affirmative imperative with a hyphen.</p>", "<p>With an affirmative <a grammar=\"Impératif\">imperative</a>, <b>en</b> is attached to the verb with a hyphen.</p>"),
        ("<p class=\"attention\">Bei <a grammar=\"Die Verben auf -er\">verbs ending in <b>&#8209;er</b></a> add <b>&#8209;s</b> to the singular imperative.</p>", "<p class=\"attention\">With <a grammar=\"Die Verben auf -er\">verbs ending in <b>&#8209;er</b></a>, add <b>&#8209;s</b> to the second-person singular affirmative imperative before <b>en</b>.</p>"),
    ],
    "07 Pronomen/10 Die unbestimmten Demonstrativpronomen.html": [
        ("<td colspan=\"4\"><b><a grammar=\"Die Demonstrativpronomen\">Demonstrativpronomen</a></b></td>", "<td colspan=\"4\"><b><a grammar=\"Die Demonstrativpronomen\">Demonstrative pronouns</a></b></td>"),
        ("<td class=\"middle center\" colspan=\"2\"><b><u>unbestimmte Form</u></b></td>", "<td class=\"middle center\" colspan=\"2\"><b><u>indefinite form</u></b></td>"),
    ],
    "07 Pronomen/14 Die Indefinitpronomen.html": [
        ("<div><span class=\"fr\">quelques-un(e)s</span> steht immer im Plural and passt sich im Geschlecht an das vertretene Substantiv an.</div>", "<div><span class=\"fr\">quelques-un(e)s</span> is always plural and agrees in gender with the noun it replaces.</div>"),
    ],
    "09 Verben/02 Die Verben auf -er.html": [
        ("<p>The <i><a grammar=\"Participe passé\">participe passé</a></i> to: <b>&#8209;é</b> formed:</p>", "<p>The <i><a grammar=\"Participe passé\">participe passé</a></i> is formed with <b>&#8209;é</b>:</p>"),
        ("<div class=\"de spoiler\">I have been <u>gesprochen</u></div>", "<div class=\"de spoiler\">I have <u>spoken</u>.</div>"),
        ("<li>In the case of verbs on <b>&#8209;cer</b> the <b>c</b> before <b>o</b> and <b>a</b> to a <b>ç</b>, to the <span class=\"ipa\">\\s\\</span>&#8209;Aussprache beizubehalten.</li>", "<li>For verbs ending in <b>&#8209;cer</b>, <b>c</b> becomes <b>ç</b> before <b>o</b> and <b>a</b> to preserve the <span class=\"ipa\">\\s\\</span> pronunciation.</li>"),
        ("<li>In the case of verbs on <b>&#8209;ger</b> is a <b>e</b> between <b>g</b> and <b>o</b>/<b>a</b> added to the <span class=\"ipa\">\\ʒ\\</span>&#8209; to be discussed.</li>", "<li>For verbs ending in <b>&#8209;ger</b>, an <b>e</b> is inserted between <b>g</b> and <b>o</b>/<b>a</b> to preserve the <span class=\"ipa\">\\ʒ\\</span> pronunciation.</li>"),
    ],
    "09 Verben/09 Reflexive Verben.html": [
        ("<p>A reflexive verb (<span class=\"fr\">verbe pronominal</span>) is always by a <a grammar=\"Die Reflexivpronomen\">Reflexivpronomen</a> begleitet (<span class=\"fr\">me, te, se, nous, vous, se</span>), which refers to the subject of the sentence.</p>", "<p>A pronominal verb (<span class=\"fr\">verbe pronominal</span>) is used with a <a grammar=\"Die Reflexivpronomen\">reflexive pronoun</a> (<span class=\"fr\">me, te, se, nous, vous, se</span>) that refers back to the subject.</p>"),
    ],
    "22 Zahlen und Zeitangaben/2 Ordnungszahlen.html": [
        ("<li>For cardinal numbers, which are based on: <b>&#8209;e</b> This is the case in the United Kingdom. <b>&#8209;e</b> weg: <span class=\"fr\">quatr<u>e</u> &rarr; quatr<u>ième</u></span>.</li>", "<li>If the cardinal number ends in <b>&#8209;e</b>, drop that <b>&#8209;e</b> before adding <b>&#8209;ième</b>: <span class=\"fr\">quatr<u>e</u> &rarr; quatr<u>ième</u></span>.</li>"),
        ("<li>Da <span class=\"fr\">premier</span> can not be connected to other numbers, one uses from 21 <span class=\"fr\">unième</span>: <span class=\"fr\">vingt et <u>unième</u></span>.</li>", "<li><span class=\"fr\">premier</span> is used only for 1st; in compound ordinals, use <span class=\"fr\">unième</span>: <span class=\"fr\">vingt et <u>unième</u></span>.</li>"),
        ("<p>In French, only for the <b>ersten</b> day of one month and for the <b>ersten</b> For dates, premier is used for the first day of a month; other dates use cardinal numbers. Regnal numbers follow their conventional forms.</p>", "<p>For dates, French uses <b>premier</b> for the first day of a month and cardinal numbers for the other days. Names of rulers likewise use the conventional French numbering forms.</p>"),
        ("<div class=\"de spoiler\">French Prime Minister</div>", "<div class=\"de spoiler\">Francis I</div>"),
        ("<h3>Expressions with ‘everyone/everyone/everyone'</h3>", "<h3>Expressions such as “every other”</h3>"),
        ("<p>An expression such as \"every other day\" is used in French with <span class=\"fr\">un/une</span> + Grundzahl + <span class=\"fr\">sur</span> + cardinal number or <span class=\"fr\">tous les/toutes les</span> + Grundzahl wiedergegeben.</p>", "<p>French can express intervals such as “every other day” with <span class=\"fr\">un/une</span> + cardinal number + <span class=\"fr\">sur</span> + cardinal number, or with <span class=\"fr\">tous les/toutes les</span> + cardinal number.</p>"),
    ],
}


def main() -> int:
    changed_files = replacements = 0
    for rel, pairs in REPLACEMENTS.items():
        path = Path("grammar") / rel
        if not path.exists():
            continue
        raw = path.read_text(encoding="utf-8")
        new = raw
        n = 0
        for old, replacement in pairs:
            if old in new:
                new = new.replace(old, replacement)
                n += 1
        if new != raw:
            path.write_text(new, encoding="utf-8")
            changed_files += 1
            replacements += n
            print(f"{rel}: reviewed page replacements={n}")
    print(f"GRAMMAR REVIEWED PAGE REPAIRS: files={changed_files} replacements={replacements}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
