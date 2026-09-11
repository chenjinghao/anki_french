#!/usr/bin/env python3
"""Reviewed English-quality repairs for stable clean-source model output.

The translation models are useful for coverage but occasionally leave German text,
translate French source-like tokens, or hallucinate legal boilerplate.  These
path-scoped substitutions repair reviewed learner-facing text while preserving all
French/IPA nodes, compatibility attributes, and legacy target element counts.
"""
from __future__ import annotations

from pathlib import Path

R: dict[str, list[tuple[str, str]]] = {
    "01 Orthografie/4 Groß- und Kleinschreibung.html": [
        ('<div class="section-title" data-topic="A2">Large and small letters</div>', '<div class="section-title" data-topic="A2">Capitalization</div>'),
        ("It 's in bold:", "French uses capital letters for:"),
        ("Satzanfänge:", "Sentence beginnings:"),
        ("Vornamen und Familiennamen:", "First and last names:"),
        ("Namen von Einwohnern (Länder, Regionen):", "Names for inhabitants of countries or regions:"),
        ('the adjectives of nationality are written in italics:', 'Nationality adjectives, however, are lowercase:'),
        ("Geografische Eigennamen (Länder, Flüsse, Gebirge):", "Geographic proper names (countries, rivers, mountain ranges):"),
        ("Cardinal directions, wenn sie als geografische Region gemeint sind:", "Cardinal directions when they refer to a geographic region:"),
        ("Namen von Festen und Feiertagen:", "Names of festivals and holidays:"),
        ("Eigennamen von Institutionen und Firmen:", "Proper names of institutions and companies:"),
        ("Religiöse Eigennamen und heilige Schriften:", "Religious proper names and sacred texts:"),
        ("Anredeformen:", "Forms of address:"),
    ],
    "01 Orthografie/5 Satzzeichen.html": [
        ('<div class="section-title" data-topic="B1">Phrase characters</div>', '<div class="section-title" data-topic="B1">Punctuation</div>'),
        ('<b>Der Punkt (.)</b> steht am Ende eines Aussagesatzes und bei vielen Abkürzungen.', '<b>The period (.)</b> ends a statement and is also used in many abbreviations.'),
        ('<b>Das Komma (,)</b> trennt Satzteile voneinander. Kein Komma steht jedoch vor notwendigen <a grammar="Relativsätze">Relativsätzen</a> und um Nebensätze mit <span class="fr">que</span> einzuleiten.', '<b>The comma (,)</b> separates parts of a sentence. French does not normally place a comma before a restrictive <a grammar="Relativsätze">relative clause</a> or simply to introduce a subordinate clause with <span class="fr">que</span>.'),
        ('<b>Das Fragezeichen (?)</b> steht am Ende einer Frage.', '<b>The question mark (?)</b> ends a question.'),
        ('<b>Das Ausrufezeichen (!)</b> folgt auf einen Ausruf oder Befehl.', '<b>The exclamation mark (!)</b> follows an exclamation or command.'),
        ('<b>Die Anführungszeichen (« »)</b>, genannt Guillemets, werden für Zitate oder direkte Rede verwendet.', '<b>French quotation marks (« »)</b>, called <i>guillemets</i>, are used for quotations and direct speech.'),
        ('<b>Der Gedankenstrich (–)</b> kennzeichnet in einem Dialog den Sprecherwechsel.', '<b>The dash (–)</b> can mark a change of speaker in dialogue.'),
        ('<p class="attention">In French it is ?, !, :, ; and in Guillemets ( ) it is a narrow vowel.</p>', '<p class="attention">French typography normally uses a space before <b>?</b>, <b>!</b>, <b>:</b>, and <b>;</b>, and spacing is also used inside <i>guillemets</i>.</p>'),
    ],
    "02 Aussprache/1 Die Aussprache.html": [
        ('The European Parliament adopted a resolution on the proposal for a directive on the approximation of the laws of the Member States.', 'voiced “zh” sound'),
    ],
    "02 Aussprache/2 Die Aussprache der Vokale.html": [
        ('<li>Der Vokal <b>a</b> ist der Stamm für die Laute <span class="ipa">\\a\\</span>, <span class="ipa">\\ɑ\\</span> und <span class="ipa">\\ə\\</span>. Im heutigen Französisch wird kaum noch zwischen <span class="ipa">\\a\\</span> und <span class="ipa">\\ɑ\\</span> unterschieden. Die Aussprache <span class="ipa">\\ə\\</span> ist meist kurz.', '<li>The vowel <b>a</b> can represent the sounds <span class="ipa">\\a\\</span>, <span class="ipa">\\ɑ\\</span>, and <span class="ipa">\\ə\\</span>. In modern French there is usually little distinction between <span class="ipa">\\a\\</span> and <span class="ipa">\\ɑ\\</span>. The sound <span class="ipa">\\ə\\</span> is usually short.'),
        ('<li>Die endings <b>&#8209;aie, &#8209;ais, &#8209;ait, &#8209;aix</b> werden <span class="ipa">\\ɛ\\</span> pronounced.', '<li>The endings <b>&#8209;aie, &#8209;ais, &#8209;ait, &#8209;aix</b> are pronounced <span class="ipa">\\ɛ\\</span>.'),
        ('<li>Das stumme <b>e</b> steht am Wort- und Silbenende und im Wortinnern zwischen Konsonanten.', '<li>Silent <b>e</b> occurs at the end of words and syllables and inside words between consonants.'),
        ('<li>Vor <b>mm</b> und <b>nn</b> wird <b>e</b> wie <b>a</b> <span class="ipa">\\a\\</span> pronounced.', '<li>Before <b>mm</b> and <b>nn</b>, <b>e</b> is pronounced like <b>a</b>, <span class="ipa">\\a\\</span>.'),
        ('<li>Ein <b>geschlossenes o</b> <span class="ipa">\\o\\</span> wird bei auslautendem <b>o</b> (auch bei stummem Schlusskonsonanten) und vor <span class="ipa">\\z\\</span> gesprochen.', '<li>A <b>close o</b> <span class="ipa">\\o\\</span> is used for final <b>o</b> (including before a silent final consonant) and before <span class="ipa">\\z\\</span>.'),
        ('<li>Ein <b>offenes o</b> <span class="ipa">\\ɔ\\</span> wird in betonter Silbe und vor Konsonant gesprochen.', '<li>An <b>open o</b> <span class="ipa">\\ɔ\\</span> is used in a stressed syllable before a pronounced consonant.'),
        ('<li>Die <b>Nasalvokale</b> <span class="ipa">\\ɛ̃\\</span>, <span class="ipa">\\ã\\</span>, <span class="ipa">\\ɔ̃\\</span>, <span class="ipa">\\œ̃\\</span> erscheinen im Schriftbild als Vokal + <b>n</b> oder <b>m</b>, werden aber als ein einziger Laut gesprochen.', '<li>The <b>nasal vowels</b> <span class="ipa">\\ɛ̃\\</span>, <span class="ipa">\\ã\\</span>, <span class="ipa">\\ɔ̃\\</span>, <span class="ipa">\\œ̃\\</span> are often written as a vowel plus <b>n</b> or <b>m</b>, but are pronounced as a single sound.'),
        ('<li>Folgt auf <b>m, mm, n</b> oder <b>nn</b> ein Vokal, wird die vorangehende Vokalverbindung nicht nasaliert.', '<li>If <b>m, mm, n</b>, or <b>nn</b> is followed by a vowel, the preceding vowel combination is not nasalized.'),
        ('<li>Die <b>Halbvokale</b> <span class="ipa">\\j\\</span>, <span class="ipa">\\w\\</span>, <span class="ipa">\\ɥ\\</span> können alleine keine Silbe bilden, sondern werden mit dem voran- oder nachstehenden Vokal zusammen pronounced.', '<li>The <b>semivowels</b> <span class="ipa">\\j\\</span>, <span class="ipa">\\w\\</span>, and <span class="ipa">\\ɥ\\</span> do not form a syllable by themselves; they are pronounced together with the neighboring vowel.'),
    ],
    "02 Aussprache/3 Die Aussprache der Konsonanten.html": [
        ('<li>Vor einem Vokal wird <b>ch</b> <span class="ipa">\\ʃ\\</span> gesprochen. Vor einem Konsonanten wird <b>ch</b> <span class="ipa">\\k\\</span> gesprochen. In Wörtern griechischen Ursprungs spricht man <b>ch</b> vor Vokal als <span class="ipa">\\k\\</span>.', '<li>Before a vowel, <b>ch</b> is normally pronounced <span class="ipa">\\ʃ\\</span>. Before a consonant it is pronounced <span class="ipa">\\k\\</span>; in some words of Greek origin, <b>ch</b> before a vowel is also <span class="ipa">\\k\\</span>.'),
        ('<li><b>f, ff, ph</b> werden <span class="ipa">\\f\\</span> gesprochen. Exception: Das f wird nicht ausgesprochen bei <span class="fr">cerf, nerf, clef</span>. Hingegen wird im Singular bei <span class="fr">bœuf, œuf</span> das f gesprochen. Bei Liaison wird f als <span class="ipa">\\v\\</span> gesprochen.', '<li><b>f, ff, ph</b> are pronounced <span class="ipa">\\f\\</span>. Exception: final <b>f</b> is silent in <span class="fr">cerf, nerf, clef</span>. In the singular forms <span class="fr">bœuf, œuf</span>, however, the <b>f</b> is pronounced. In liaison, <b>f</b> can be pronounced <span class="ipa">\\v\\</span>.'),
        ('<li><b>g</b> am Wortende ist stumm.', '<li>Final <b>g</b> is silent.'),
        ('<li>Das <b>h</b> ist immer stumm. Man unterscheidet zwischen <b>h muet</b> (stummes h) und <b><a grammar="Das h aspiré">h aspiré</a></b> (behauchtes h).', '<li>The letter <b>h</b> itself is silent. French distinguishes <b>h muet</b> (mute h) from <b><a grammar="Das h aspiré">h aspiré</a></b> (aspirated h).'),
        ('<li>Das <b>h muet</b> hat keinerlei Einfluss auf die Aussprache. Es wird wie ein Vokal behandelt, d.h. es findet Elision und Liaison statt.', '<li><b>h muet</b> behaves like a vowel-initial word for elision and liaison.'),
        ("<li>Das <b>h aspiré</b> ist ein stimmloser Konsonant und beeinflusst die Aussprache seiner Umgebung. Es verhindert Liaison und Elision. Im Wörterbuch wird h aspiré mit einem ' gekennzeichnet.", '<li><b>h aspiré</b> blocks both liaison and elision even though the <b>h</b> itself is not pronounced. Dictionaries often mark such words specially.'),
        ('<li><b>s</b> ist zwischen Vokalen immer stimmhaft <span class="ipa">\\z\\</span>. Exception: Nach Nasalvokal ist s stimmlos <span class="ipa">\\s\\</span>.', '<li>Between vowels, <b>s</b> is normally voiced <span class="ipa">\\z\\</span>. After a nasal vowel it can remain voiceless <span class="ipa">\\s\\</span>.'),
        ('<li>Die ending <b>&#8209;tie</b> wird in Wörtern griechischen Ursprungs <span class="ipa">\\si\\</span> gesprochen.', '<li>The ending <b>&#8209;tie</b> is pronounced <span class="ipa">\\si\\</span> in many words of Greek origin.'),
        ('<span class="warning">Ausnahme</span>:', '<span class="warning">Exception</span>:'),
        ('<li><b>y</b> wird allein oder in konsonantischer Umgebung <span class="ipa">\\i\\</span> gesprochen. In vokalischer Umgebung wird y <span class="ipa">\\j\\</span> oder <span class="ipa">\\ij\\</span> gesprochen.', '<li><b>y</b> is pronounced <span class="ipa">\\i\\</span> on its own or next to consonants. In a vowel context it is pronounced <span class="ipa">\\j\\</span> or <span class="ipa">\\ij\\</span>.'),
    ],
    "02 Aussprache/5 Die Liaison.html": [
        ('In the <b class="tag-lemma">Liaison</b> (binding)', 'In <b class="tag-lemma">liaison</b>'),
        ('One distinguishes between binding, forbidden and optional liaisons.', 'French distinguishes mandatory, forbidden, and optional liaisons.'),
        ('With a <b><a grammar="Das h aspiré">h aspiré</a></b> (breathing h) finds <b>I never did.</b> The consonant is not bound.', 'With <b><a grammar="Das h aspiré">h aspiré</a></b>, <b>liaison never occurs</b>; the final consonant is not linked to the following word.'),
        ('<h3>Liability liabilities (<i> Liaisons obligatoires</i>)</h3>', '<h3>Mandatory liaisons (<i>liaisons obligatoires</i>)</h3>'),
        ('The liaison shall be binding in the following cases:', 'Liaison is mandatory in the following cases:'),
        ('Determinant/Zahl + Substantiv', 'Determiner/number + noun'),
        ('Vorangestelltes Adjektiv + Substantiv', 'Preposed adjective + noun'),
        ('Einsilbige Präposition + Nomen', 'One-syllable preposition + noun'),
        ('Einsilbiges Adverb + Adjektiv', 'One-syllable adverb + adjective'),
        ('Substantiv | Verb', 'Noun | verb'),
        ('Substantiv (Singular) | Adjektiv', 'Singular noun | adjective'),
        ('Nach Frageadverbien (außer bei Ausnahmen)', 'After interrogative adverbs (except in some set expressions)'),
        ('nach <b>s</b>, <b>x</b>, <b>z</b> (ca. 50% aller Liaisons)', 'after <b>s</b>, <b>x</b>, <b>z</b> (about 50% of liaisons)'),
        ('nach <b>t</b>, <b>d</b> (ca. 25% aller Liaisons)', 'after <b>t</b>, <b>d</b> (about 25% of liaisons)'),
        ('nach <b>n</b> (ca. 25% aller Liaisons)', 'after <b>n</b> (about 25% of liaisons)'),
        ('nach <b>r</b>', 'after <b>r</b>'),
        ('nach <b>p</b> (fast nur nach <span class="fr">beaucoup</span> und <span class="fr">trop</span>)', 'after <b>p</b> (mostly after <span class="fr">beaucoup</span> and <span class="fr">trop</span>)'),
        ('in sehr seltenen Fällen', 'in very rare cases'),
        ('nach <span class="fr tag-lemma">neuf</span> (nur vor <span class="fr">ans</span> und <span class="fr">heures</span>)', 'after <span class="fr tag-lemma">neuf</span> (only before <span class="fr">ans</span> and <span class="fr">heures</span>)'),
        ('Verb + pronouns (bei <a grammar="Inversion">Inversion</a>)', 'Verb + pronoun (with <a grammar="Inversion">inversion</a>)'),
        ('Nach <span class="fr tag-lemma">quand</span>, <span class="fr tag-lemma">dont</span>', 'After <span class="fr tag-lemma">quand</span> and <span class="fr tag-lemma">dont</span>'),
        ('Nach dem Fragepronomen bei Inversion: <b>Verb | pronouns</b>', 'After an interrogative pronoun with inversion: <b>verb | pronoun</b>'),
        ('Vor <span class="fr tag-lemma">huit</span>, <span class="fr tag-lemma">onze</span>, <span class="fr tag-lemma">oui</span>', 'Before <span class="fr tag-lemma">huit</span>, <span class="fr tag-lemma">onze</span>, and <span class="fr tag-lemma">oui</span>'),
        ('Nach <span class="fr tag-lemma">et</span>', 'After <span class="fr tag-lemma">et</span>'),
        ('Nach dem <a grammar="Modal- und Hilfsverben">auxiliary verb</a> <span class="fr tag-lemma">être</span>', 'After the <a grammar="Modal- und Hilfsverben">auxiliary verb</a> <span class="fr tag-lemma">être</span>'),
        ('Zwischen dem Verb <b>être</b> und dem folgenden Attribut', 'Between <b>être</b> and the following complement'),
    ],
    "03 Artikel/1 Der bestimmte Artikel.html": [
        ('<p class="highlight">For nouns used with a vowel or <a grammar="Das h aspiré">silent h</a> The following articles shall be published in the Official Journal of the European Union: <span class="fr">le</span> and <span class="fr">la</span> to <span class="fr">l\'</span> This process is called elision.</p>', '<p class="highlight">Before a vowel or <a grammar="Das h aspiré">silent h</a>, <span class="fr">le</span> and <span class="fr">la</span> contract to <span class="fr">l\'</span>. This process is called elision.</p>'),
    ],
    "03 Artikel/3 Der Teilungsartikel.html": [
        ('<p>He\'s going to get out of the preposition <span class="fr tag-lemma">de</span> and the <a grammar="Der bestimmte Artikel">definite article</a> I\'ve been educated.</p>', '<p>The partitive article is formed from the preposition <span class="fr tag-lemma">de</span> plus the <a grammar="Der bestimmte Artikel">definite article</a>.</p>'),
        ('Im Singular für nicht zählbare Dinge und abstrakte Begriffe:', 'In the singular for uncountable things and abstract concepts:'),
        ('Im Plural für eine unbestimmte Anzahl zählbarer Dinge:', 'In the plural for an indefinite number of countable things:'),
        ('After one <a grammar="Verneinung">Denial</a> the partitive article', 'After <a grammar="Verneinung">negation</a>, the partitive article'),
        ('If in the plural an adjective is before the noun,', 'When an adjective precedes a plural noun,'),
    ],
    "04 Substantive/01 Das Geschlecht der Substantive.html": [
        ('<p>In French there are only masculine and feminine nouns. The German neutrum does not exist. The grammatical gender may differ from the German (e.g. <span class="fr">la mort</span> death, <span class="fr">le vase</span> the vase).</p>', '<p>French nouns are either masculine or feminine. Grammatical gender is not reliably predictable from English meaning, so learn each noun together with its article (for example, <span class="fr">la mort</span> “death” and <span class="fr">le vase</span> “vase”).</p>'),
        ('The grammatical gender of things and things', 'The grammatical gender of inanimate nouns'),
        ('This Regulation shall enter into force on the twentieth day following that of its publication in the Official Journal of the European Union.', 'Cambodia'),
        ('The Commission shall adopt delegated acts in accordance with the opinion of the European Parliament and of the Council.', 'Mozambique'),
        ('The Commission shall adopt implementing acts in accordance with the opinion of the European Parliament and of the Council.', 'Zimbabwe'),
        ('grammatiical gender', 'grammatical gender'),
    ],
    "04 Substantive/02 Das Geschlecht bei bestimmten Wortendungen.html": [
        ('<p class="attention">In German nouns are <b>- age</b> and <b>- own</b> female (<i>The garage, the driveway.</i>), but in French they are male.</p>', '<p class="attention">French nouns ending in <b>&#8209;age</b> and <b>&#8209;ège</b> are typically masculine (for example, <i>le garage, le manège</i>).</p>'),
    ],
    "05 Adjektive/4 Adjektive mit zwei männlichen Formen.html": [
        ('Adjectives with two male forms', 'Adjectives with two masculine forms'),
    ],
    "06 Adverbien/1 Die Formen von Adverbien.html": [
        ('<b>Female form</b>', '<b>feminine form</b>'),
        ('<b>Male form</b>', '<b>masculine form</b>'),
        ('The adverb is formed by using the ending <b>- ment</b> to the <a grammar="Adjektive in der Femininform"><b>feminine form</b> of the adjective</a> It\'s on.', 'An adverb is usually formed by adding <b>&#8209;ment</b> to the <a grammar="Adjektive in der Femininform"><b>feminine form</b> of the adjective</a>.'),
        ('For adjectives ending in an audible vowel (but not in <b>&#8209;e</b>), will be <b>- ment</b> to the <b>masculine form</b> It\'s attached.', 'For adjectives ending in a pronounced vowel other than <b>&#8209;e</b>, add <b>&#8209;ment</b> to the <b>masculine form</b>.'),
        ('Adjectives derived from adjectives', 'Adverbs derived from adjectives'),
        ('Adjectives of the given time:', 'Adverbs of a specific time:'),
        ('Adjectives of the indefinite period:', 'Adverbs of an indefinite time:'),
        ('Adjectives of the way:', 'Adverbs of manner:'),
        ('adverbs of the set:', 'Adverbs of quantity:'),
    ],
    "07 Pronomen/01 Die verbundenen Personalpronomen.html": [
        ('<div class="section-title" data-topic="A1">The related personal pronouns <small>(je, il)</small></div>', '<div class="section-title" data-topic="A1">Clitic personal pronouns <small>(je, il)</small></div>'),
        ('<p>In French there is no equivalent to the German personal pronoun <span class="de">It \'s</span>In the French language, only masculine and feminine forms are known. <span class="fr">il</span> or <span class="fr">elle</span>, depending on whether they are male or female persons or objects, for example:</p>', '<p>French has no neuter subject pronoun that directly corresponds to English <span class="de">it</span>. Use <span class="fr">il</span> or <span class="fr">elle</span> according to the grammatical gender of the noun being referred to, for example:</p>'),
        ('<p>While in German <span class="de">They</span> in the third person plural is used for both sexes, the French distinguishes between <span class="fr">ils</span> (male) and <span class="fr">elles</span> (female), for example:</p>', '<p>English <span class="de">they</span> does not mark grammatical gender, whereas French distinguishes <span class="fr">ils</span> (masculine or mixed groups) from <span class="fr">elles</span> (all-feminine groups), for example:</p>'),
    ],
    "07 Pronomen/08 Die Demonstrativpronomen.html": [
        ('das Demonstrativpronomen wird mit <span class="fr">de</span> ergänzt:', 'the demonstrative pronoun is followed by <span class="fr">de</span>:'),
        ('auf das Demonstrativpronomen folgt ein <a grammar="Relativsätze">Relativsatz</a>:', 'the demonstrative pronoun is followed by a <a grammar="Relativsätze">relative clause</a>:'),
        ('<p>In addition to the simple forms of the demonstrative pronoun, there are the compound forms with <span class="fr">&#8209;ci</span> and <span class="fr">&#8209;là</span>Demonstrative pronouns with <span class="fr">&#8209;ci</span> The demonstrative pronouns are used to refer to something that is in the immediate vicinity of the speaker. <span class="fr">&#8209;là</span> pointing to something farther away.</p>', '<p>Besides the simple forms, demonstrative pronouns have compound forms with <span class="fr">&#8209;ci</span> and <span class="fr">&#8209;là</span>. Forms with <span class="fr">&#8209;ci</span> point to something nearer the speaker, while forms with <span class="fr">&#8209;là</span> point to something farther away.</p>'),
    ],
    "07 Pronomen/09 Die Demonstrativbegleiter.html": [
        ('<span class="de">This is not the case.</span>', '<span class="de">this/these</span>'),
        ('<span class="de">The Commission shall adopt delegated acts in accordance with the opinion of the European Parliament and of the Council.</span>', '<span class="de">that/those</span>'),
    ],
    "07 Pronomen/13 Die Indefinitbegleiter.html": [
        ('The indefinite companions', 'Indefinite determiners'),
        ('<p>An indefinite determiner is a noun. It denotes an indefinite quantity or an indeterminate identity.</p>', '<p>An indefinite determiner accompanies a noun and expresses an indefinite quantity or identity.</p>'),
    ],
    "12 Passiv/1 Das Passif.html": [
        ('<p>In <b>passif</b> (passive), the subject is not the actor, but the recipient of the action. The passive is used less frequently in French than in German and occurs mainly in written language.</p>', '<p>In the <b>passif</b> (passive voice), the subject receives the action rather than performing it. French often prefers an active or impersonal construction where English can also use a passive, though the passive remains common in formal and written French.</p>'),
        ('<p>The liability consists of:', '<p>The passive is formed with:'),
        ('<p>The operator is normally introduced with the preposition', '<p>The agent is normally introduced with the preposition'),
    ],
    "14 Relativsätze/4 Relativsätze mit lequel.html": [
        ('<div class="attention">Diese Formen werden nur verwendet, wenn ihnen eine Präposition vorangeht. Für einfache Ergänzungen mit <b>de</b> wird im Relativsatz <b>dont</b> benutzt.', '<div class="attention">These forms are used when a preposition precedes the relative pronoun. For a simple complement with <b>de</b>, use <b>dont</b> instead.'),
    ],
    "18 Verneinung/01 Verneinungswörter.html": [
        ('<p>In French, denial usually consists of two parts: <span class="fr tag-lemma rounded-border">ne</span> (or <span class="fr">n’</span> before vowel or <a grammar="Das h aspiré">silent h</a>This differs from German, where the refusal usually consists of only one word.</p>', '<p>French negation commonly has two parts: <span class="fr tag-lemma rounded-border">ne</span> (or <span class="fr">n’</span> before a vowel or <a grammar="Das h aspiré">silent h</a>) plus a second negative word such as <span class="fr">pas</span>.</p>'),
    ],
    "18 Verneinung/04 Verneinung ohne ne.html": [
        ('<div class="section-title" data-topic="B2">Denial without <i>ne</i></div>', '<div class="section-title" data-topic="B2">Negation without <i>ne</i></div>'),
        ('<p>For verbs, in the formal language, both parts of the negative verb (<span class="fr"><span class="tag-lemma">ne</span> ... <span class="tag-lemma">pas</span></span>) must surround the verb; however, for other word types, <span class="fr">pas</span> is often used without <span class="fr">ne</span>.</p>', '<p>In formal French, <span class="fr"><span class="tag-lemma">ne</span> ... <span class="tag-lemma">pas</span></span> normally surrounds a conjugated verb. With adjectives, adverbs, nouns, and pronouns, <span class="fr">pas</span> can appear without <span class="fr">ne</span>.</p>'),
        ('<h3><i>pas</i> + fixed rotation</h3>', '<h3><i>pas</i> + fixed expression</h3>'),
    ],
    "22 Zahlen und Zeitangaben/2 Ordnungszahlen.html": [
        ('The order numbers', 'Ordinal numbers'),
        ('The order numbers are formed by adding the end', 'Ordinal numbers are formed by adding the ending'),
        ('the corresponding base number', 'the corresponding cardinal number'),
        ('Date and date of establishment', 'Dates and rulers'),
        ('serial numbers', 'ordinal numbers'),
    ],
    "22 Zahlen und Zeitangaben/3 Bruchzahlen.html": [
        ('<div class="section-title" data-topic="A2">Breakdowns</div>', '<div class="section-title" data-topic="A2">Fractions</div>'),
        ('<p>Most fractional numbers are derived from ordinal numbers. <a grammar="Ordnungszahlen">Order number</a>.</p>', '<p>Most fractions are formed from <a grammar="Ordnungszahlen">ordinal numbers</a>.</p>'),
        ('The exceptions are the first three breaches:', 'The first three fractions are exceptions:'),
    ],
    "99 Vokabeln/04 Emotionen und Charakter.html": [
        ('Other, not further worked than hot-rolled, impregnated, coated or covered with plastics', 'inferior; lower'),
    ],
    "99 Vokabeln/28 Falsche Freunde.html": [
        ('The Commission shall adopt implementing acts in accordance with the procedure referred to in paragraph 1 of this Article.', 'delay; lateness'),
    ],
    "_/VerbenBringenMitnehmen.html": [
        ('The Commission shall adopt implementing acts in accordance with the procedure referred to in paragraph 1 of this Article.', 'take away'),
    ],
}


def apply(path: Path) -> int:
    rel = str(path.relative_to("grammar"))
    rules = R.get(rel)
    if not rules:
        return 0
    raw = path.read_text(encoding="utf-8")
    new = raw
    changes = 0
    for old, replacement in rules:
        count = new.count(old)
        if count:
            new = new.replace(old, replacement)
            changes += count
    if new != raw:
        path.write_text(new, encoding="utf-8")
        print(f"{rel}: reviewed-v6 replacements={changes}")
    return changes


def main() -> int:
    files = total = 0
    for path in sorted(Path("grammar").rglob("*.html")):
        count = apply(path)
        if count:
            files += 1
            total += count
    print(f"GRAMMAR REVIEWED REPAIRS V6: files={files} replacements={total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
