#!/usr/bin/env python3
"""Reviewed semantic cleanup for errors missed by the original regex QA.

These path-scoped substitutions remove residual German, legal-text hallucinations,
and obviously mistranslated grammar terminology found during manual review of the
zero-finding candidate. They change learner-facing text only.
"""
from __future__ import annotations

from pathlib import Path

R: dict[str, list[tuple[str, str]]] = {
    "01 Orthografie/2 Der Akzent.html": [
        ('<p>On the <b>(a) for the purposes of this Regulation</b> and <b>U</b> Accent grave is used to distinguish words that sound the same but have different meanings (so-called <b>Homonyms</b>).</p>',
         '<p>On <b>a</b> and <b>u</b>, the accent grave can distinguish words that sound the same but have different meanings (so-called <b>homonyms</b>).</p>'),
    ],
    "02 Aussprache/6 Die Aussprache von plus.html": [
        ('<div class="de spoiler">It \'s not a single cake . <u>more</u> The Commission has not yet taken a decision.<span class="ipa">\\plyz ɛ̃\\</span> or <span class="ipa">\\ply ɛ̃\\</span>)</div>',
         '<div class="de spoiler">There is not a single cake <u>left</u>. (<span class="ipa">\\plyz ɛ̃\\</span> or <span class="ipa">\\ply ɛ̃\\</span>)</div>'),
    ],
    "03 Artikel/1 Der bestimmte Artikel.html": [
        ('<li>bei Verallgemeinerungen:', '<li>for general statements:'),
        ('<li>bei Titeln:', '<li>with titles:'),
        ('<li>bei Körperteilen:', '<li>with body parts:'),
        ('<li>bei Languages und festen Wendungen:', '<li>with languages and fixed expressions:'),
    ],
    "04 Substantive/01 Das Geschlecht der Substantive.html": [
        ('<li>Länder, die nicht auf &#8209;e enden:', '<li>Countries that do not end in &#8209;e:'),
    ],
    "04 Substantive/02 Das Geschlecht bei bestimmten Wortendungen.html": [
        ('of a noun. The following lists show typical male and female endings.', 'of a noun. The following lists show typical masculine and feminine endings.'),
        ('♀ Female finishes', '♀ Typical feminine endings'),
        ('♂ Male finishes', '♂ Typical masculine endings'),
    ],
    "04 Substantive/04 Zusammengesetzte Substantive.html": [
        ('<span class="de">Vice-President of the Commission</span>', '<span class="de">vice-president</span>'),
    ],
    "07 Pronomen/04 Die indirekten Objektpronomen.html": [
        ('<p>For male and female dating objects, there is only one indirect object pronoun.</p>',
         '<p>The same indirect-object pronoun forms are used regardless of the person\'s gender.</p>'),
    ],
    "07 Pronomen/12 Die Possessivpronomen.html": [
        ('<p>The possessive pronouns (<span class="fr">pronoms possessifs</span>) in genus and numerus correspond to the nomenclature they replace. <a grammar="Die Possessivbegleiter">Accompanying possessions</a> (<i>mon</i>, <i>ton</i>, etc.) substitute possessive pronouns for the reference noun completely. <a grammar="Der bestimmte Artikel">definite article</a> used:</p>',
         '<p>Possessive pronouns (<span class="fr">pronoms possessifs</span>) agree in gender and number with the noun they replace. Unlike <a grammar="Die Possessivbegleiter">possessive determiners</a> (<i>mon</i>, <i>ton</i>, etc.), they replace the noun completely and are always used with the <a grammar="Der bestimmte Artikel">definite article</a>:</p>'),
        ('<th>of a kind used for the manufacture of foodstuffs</th>', '<th>Masculine</th>'),
        ('<th>Female</th>', '<th>Feminine</th>'),
        ('<td>I am very pleased with this report.</td>', '<td>mine</td>'),
        ('<td>(i.e. in the case of your</td>', '<td>yours</td>'),
        ('<td>In the case of the United Kingdom, the Commission shall take into account the information provided by the Member State concerned.<br>(i) the number of persons who are not members of the family;</td>', '<td>his / hers</td>'),
        ('<td>We are not going to be able to do that.</td>', '<td>ours</td>'),
        ('<td>your, your/your<br>(b) the Commission\'s proposal for a regulation on the protection of workers\' rights;</td>', '<td>yours</td>'),
        ('<td>(i) the amount of aid granted by the Member State concerned to the beneficiary of the aid;</td>', '<td>theirs</td>'),
        ('<h3><i>À moi</i> or <i>le mien</i>?</h3>', '<h3><i>À moi</i> or <i>le mien</i>?</h3>'),
        ('<p>The Structures <span class="fr">"à moi"</span> and <span class="fr">"le mien"</span> They can be used similarly in many situations, but have subtle differences:</p>',
         '<p>The structures <span class="fr">"à moi"</span> and <span class="fr">"le mien"</span> can be used similarly in many situations, but there are subtle differences:</p>'),
        ('<li><span class="fr">"C\'est à moi"</span>: Rather informal and emotional. Often used to claim something for itself that its owner is not clear. Can express pride or possession greed.</li>',
         '<li><span class="fr">"C\'est à moi"</span>: More informal and emphatic. It is often used to claim ownership when the owner is not obvious.</li>'),
        ('<li><span class="fr">"C\'est le mien"</span>: Descriptive and often implies that the object has been in possession for longer.</li>',
         '<li><span class="fr">"C\'est le mien"</span>: More descriptive and often used when the object has already been identified in the conversation.</li>'),
        ('<td>Le mien / la mienne / le mien (s)</td>', '<td>le mien / la mienne / les mien(ne)s</td>'),
        ('<td>Le tien / la tienne / les tien(ne) of the Spanish language</td>', '<td>le tien / la tienne / les tien(ne)s</td>'),
        ('<td>Le sien / la sienne / le sien(ne) is the name of the country in which it is located.</td>', '<td>le sien / la sienne / les sien(ne)s</td>'),
        ('<td>Le Notre / the Notre / the Our</td>', '<td>le nôtre / la nôtre / les nôtres</td>'),
        ('<td>Le vôtre / la vôtre / les vôtres is the name given to a group of</td>', '<td>le vôtre / la vôtre / les vôtres</td>'),
        ('<td>Le Leur / La Leur / Leur</td>', '<td>le leur / la leur / les leurs</td>'),
    ],
    "09 Verben/01 Das Verb.html": [
        ('<li>One of them <b>Action</b>, e.g. <span class="fr">manger</span> (<span class="de">eating</span>), <span class="fr">parler</span> (<span class="de">Speaking</span>)</li>',
         '<li>an <b>action</b>, e.g. <span class="fr">manger</span> (<span class="de">to eat</span>), <span class="fr">parler</span> (<span class="de">to speak</span>)</li>'),
        ('<li>One of them <b>State of operation</b>, e.g. <span class="fr">être</span> (<span class="de">be</span>), <span class="fr">sembler</span> (<span class="de">They seem to be</span>)</li>',
         '<li>a <b>state</b>, e.g. <span class="fr">être</span> (<span class="de">to be</span>), <span class="fr">sembler</span> (<span class="de">to seem</span>)</li>'),
        ('<li>or a <b>Events</b>, e.g. <span class="fr">pleuvoir</span> (<span class="de">raining</span>), <span class="fr">arriver</span> (<span class="de">Arriving</span>)</li>',
         '<li>or an <b>event</b>, e.g. <span class="fr">pleuvoir</span> (<span class="de">to rain</span>), <span class="fr">arriver</span> (<span class="de">to arrive</span>)</li>'),
        ('<p>The <a grammar="Der Infinitiv">Infinitive</a> In French it ends up <b>- they</b>, <b>- their</b>, <b>- of which:</b> or <b>- other than:</b>. These endings determine the membership of a conjugation group and hence the respective endings in the different timeforms.</p>',
         '<p>The French <a grammar="Der Infinitiv">infinitive</a> typically ends in <b>&#8209;er</b>, <b>&#8209;ir</b>, <b>&#8209;re</b>, or <b>&#8209;oir</b>. These endings help identify the conjugation group and its patterns.</p>'),
        ('<p class="highlight">The French verbs are divided into three main conjugation groups. The verbs on <span class="fr">&#8209;oir</span> form their own group of irregular verbs.</p>',
         '<p class="highlight">French verbs are usually grouped by infinitive ending. Verbs in <span class="fr">&#8209;oir</span> are irregular and are commonly learned as a separate set.</p>'),
        ('<p><b><a grammar="Die Verben auf -er"> Verbs on which:</a></b></p>', '<p><b><a grammar="Die Verben auf -er">Verbs ending in &#8209;er:</a></b></p>'),
        ('<p><b><a grammar="Die Verben auf -ir"> Verbs on which:</a></b></p>', '<p><b><a grammar="Die Verben auf -ir">Verbs ending in &#8209;ir:</a></b></p>'),
        ('<p><b><a grammar="Die Verben auf -re">Verbs on \'re</a> and <a grammar="Die Verben auf -oir">Verbs on ‐oir</a>:</b></p>', '<p><b><a grammar="Die Verben auf -re">Verbs ending in &#8209;re</a> and <a grammar="Die Verben auf -oir">&#8209;oir</a>:</b></p>'),
        ('<p>Innerhalb dieser Gruppen wird zwischen regelmäßigen und unregelmäßigen Verben unterschieden. Zusätzlich lassen sich Verben nach ihrer Funktion einteilen in <b>Vollverben</b>, <a grammar="Modal- und Hilfsverben"><b>Hilfsverben</b>, <b>Modalverben</b></a>, <a grammar="Reflexive Verben"><b>reflexive Verben</b></a> und <a grammar="Unpersönliche Verben"><b>unpersönliche Verben</b></a>.',
         '<p>Within these groups, verbs may be regular or irregular. By function, French verbs can also be classified as <b>main verbs</b>, <a grammar="Modal- und Hilfsverben"><b>auxiliary verbs</b> and <b>modal verbs</b></a>, <a grammar="Reflexive Verben"><b>reflexive verbs</b></a>, and <a grammar="Unpersönliche Verben"><b>impersonal verbs</b></a>.'),
        ('<div class="de spoiler">Thomas <u>eat</u> It\'s an apple.</div>', '<div class="de spoiler">Thomas <u>eats</u> an apple.</div>'),
        ('<div class="de spoiler">We are <u>Playing</u> You know, chess.</div>', '<div class="de spoiler">We <u>play</u> chess.</div>'),
        ('<div class="de spoiler">You <u>terminate</u> their meals.</div>', '<div class="de spoiler">They <u>finish</u> their meal.</div>'),
        ('<div class="de spoiler">The baby <u>sleeps</u> It\'s all right.</div>', '<div class="de spoiler">The baby <u>sleeps</u> well.</div>'),
        ('<div class="de spoiler">I got my hat. <u>Lost</u>.</div>', '<div class="de spoiler">I <u>lost</u> my hat.</div>'),
        ('<div class="de spoiler">He did. <u>receives</u> It\'s an award.</div>', '<div class="de spoiler">He <u>receives</u> an award.</div>'),
    ],
    "09 Verben/03 Die Verben auf -ir.html": [
        ('<div class="section-title" data-topic="A2">The verbs on them</div>', '<div class="section-title" data-topic="A2">Verbs ending in &#8209;ir</div>'),
        ('<p>The group of verbs on <b> ‐ir</b> includes about 300 verbs, which are mostly regular.</p>', '<p>The <b>&#8209;ir</b> group contains about 300 verbs. Many follow regular patterns, with two important subgroups.</p>'),
        ('<p>These verbs extend the stem into the plural forms (<span class="fr">nous, vous, ils/elles</span>) with: <b>- I\'m not sure.</b>That \'s it . <i><a grammar="Participe passé">Participe passé</a></i> Ends up <b>-i</b>.</p>', '<p>These verbs add <b>&#8209;iss&#8209;</b> to the stem in the plural forms (<span class="fr">nous, vous, ils/elles</span>). Their <i><a grammar="Participe passé">participe passé</a></i> normally ends in <b>&#8209;i</b>.</p>'),
        ('<span class="de">Select</span>', '<span class="de">to choose</span>'),
        ('<span class="de">Growing</span>', '<span class="de">to grow</span>'),
        ('<span class="de">punished</span>', '<span class="de">to punish</span>'),
        ('<span class="de">reacting</span>', '<span class="de">to react</span>'),
        ('<span class="de">I think it\'s better than that.</span>', '<span class="de">to think; to reflect</span>'),
        ('<span class="de">Filling</span>', '<span class="de">to fill</span>'),
        ('<span class="de">Successful</span>', '<span class="de">to succeed</span>'),
        ('<p>These verbs hang the end directly on the stem. The stem is often abbreviated in the singular forms. <i>Participe passé</i> Ends up <b>-i</b>.</p>', '<p>These verbs attach the endings directly to the stem, which is often shortened in the singular. Their <i>participe passé</i> normally ends in <b>&#8209;i</b>.</p>'),
        ('<span class="de">agreed to</span>', '<span class="de">to consent</span>'),
        ('<span class="de">You \'re lying .</span>', '<span class="de">to lie</span>'),
        ('<span class="de">departure/departure</span>', '<span class="de">to leave</span>'),
        ('<span class="de">Going out</span>', '<span class="de">to go out</span>'),
        ('<p class="attention"><b>Exception: Verbs such as <span class="fr">ouvrir</span></b><br>\n    Verbs such as <span class="fr">ouvrir</span> (<span class="de">Opening</span>), <span class="fr">couvrir</span> (<span class="de">to cover</span>), <span class="fr">découvrir</span> (<span class="de">to discover</span>), <span class="fr">offrir</span> (<span class="de">offer/donate</span>) and <span class="fr">souffrir</span> (<span class="de">suffering</span>) are used in the present as verbs <b>- they</b> You know, you\'re conjoined. <i>Participe passé</i> Ends up <b>- your</b>.</p>', '<p class="attention"><b>Exception: verbs such as <span class="fr">ouvrir</span></b><br>\n    Verbs such as <span class="fr">ouvrir</span> (<span class="de">to open</span>), <span class="fr">couvrir</span> (<span class="de">to cover</span>), <span class="fr">découvrir</span> (<span class="de">to discover</span>), <span class="fr">offrir</span> (<span class="de">to offer</span>), and <span class="fr">souffrir</span> (<span class="de">to suffer</span>) conjugate like regular <b>&#8209;er</b> verbs in the present. Their <i>participe passé</i> ends in <b>&#8209;ert</b>.</p>'),
    ],
    "09 Verben/04 Die Verben auf -re.html": [
        ('<div class="section-title" data-topic="B1">The verbs on \'re</div>', '<div class="section-title" data-topic="B1">Verbs ending in &#8209;re</div>'),
        ('<p>There are about 180 verbs on <b>- of which:</b>Many of these are irregular, but there is a small group of regular verbs, e.g. <span class="fr">vendre</span> (<span class="de">to sell</span>).</p>', '<p>There are about 180 verbs ending in <b>&#8209;re</b>. Many are irregular, but a small group follows a regular pattern, for example <span class="fr">vendre</span> (<span class="de">to sell</span>).</p>'),
        ('<p>The periodic closures in the <a grammar="Présent">Presence</a> They say: <b>\'s, -s, -, -ons, -ez, -ent</b>That \'s it . <i><a grammar="Participe passé">Participe passé</a></i> Ends up <b>- you</b>.</p>', '<p>The <a grammar="Présent">present-tense</a> endings are <b>&#8209;s, &#8209;s, ∅, &#8209;ons, &#8209;ez, &#8209;ent</b>. The regular <i><a grammar="Participe passé">participe passé</a></i> ends in <b>&#8209;u</b>.</p>'),
        ('<span class="de">Listening</span>', '<span class="de">to hear</span>'),
        ('<span class="de">Waiting</span>', '<span class="de">to wait</span>'),
        ('<span class="de">answering questions</span>', '<span class="de">to answer</span>'),
        ('<span class="de">Losing</span>', '<span class="de">to lose</span>'),
        ('<span class="de">defending</span>', '<span class="de">to defend</span>'),
        ('<span class="de">dependent</span>', '<span class="de">to depend</span>'),
        ('<span class="de">to stretch, to get rich</span>', '<span class="de">to stretch; to hold out</span>'),
        ('<span class="de">claiming</span>', '<span class="de">to claim; to pretend</span>'),
        ('<span class="de">spreading</span>', '<span class="de">to spread</span>'),
        ('<span class="de">Going down</span>', '<span class="de">to go down</span>'),
        ('<span class="de">Suspended, suspended</span>', '<span class="de">to suspend</span>'),
        ('<span class="de">mixed</span>', '<span class="de">to confuse</span>'),
        ('<span class="de">melting</span>', '<span class="de">to melt</span>'),
        ('<span class="de">Relaxation</span>', '<span class="de">to relax</span>'),
        ('<span class="de">Bites and stings</span>', '<span class="de">to bite</span>'),
        ('<span class="de">hanging</span>', '<span class="de">to hang</span>'),
    ],
    "09 Verben/05 Die Verben auf -oir.html": [
        ('<div class="section-title" data-topic="B1">The verbs on ‐oir</div>', '<div class="section-title" data-topic="B1">Verbs ending in &#8209;oir</div>'),
        ('<p>The verbs on <b> ‐oir</b> are irregular and must be learned individually.</p>', '<p>Verbs ending in <b>&#8209;oir</b> are irregular and must largely be learned individually.</p>'),
        ('<span class="de">Knowing</span>', '<span class="de">to know</span>'),
        ('<span class="de">Seeing</span>', '<span class="de">to see</span>'),
        ('<span class="de">Foreseeable, planned</span>', '<span class="de">to foresee; to plan</span>'),
        ('<span class="de">See you again.</span>', '<span class="de">to see again</span>'),
        ('<span class="de">Provision is made to ensure that:</span>', '<span class="de">to provide for</span>'),
        ('<span class="de">Seeing and guessing.</span>', '<span class="de">to glimpse</span>'),
        ('<span class="de">receiving, receiving</span>', '<span class="de">to receive</span>'),
        ('<span class="de">designing, designing</span>', '<span class="de">to conceive; to design</span>'),
        ('<span class="de">Disappointment</span>', '<span class="de">to disappoint</span>'),
        ('<span class="de">overwhelming, self-imposed</span>', '<span class="de">to prevail</span>'),
        ('<span class="de">(Sitting)</span>', '<span class="de">to sit; to seat</span>'),
        ('<span class="de">Moving</span>', '<span class="de">to move</span>'),
        ('<span class="de">Promote and promote</span>', '<span class="de">to promote</span>'),
        ('<span class="de">Moving, moving</span>', '<span class="de">to move emotionally</span>'),
        ('<span class="de">raining</span>', '<span class="de">to rain</span>'),
    ],
    "10 Zeitformen und Modi/12 Subjonctif.html": [
        ('<span class="fr">proposer</span> (Proposal for a Council Regulation)', '<span class="fr">proposer</span> (to propose; to suggest)'),
    ],
    "11 Partizip/3 Participe passé.html": [
        ('<li>Als Adverbialbestimmung (verkürzt einen Nebensatz):', '<li>As an adverbial phrase (shortening a subordinate clause):'),
        ('<li>Als Adjektiv (attributiv oder prädikativ):', '<li>As an adjective (attributive or predicative):'),
        ('<li>Mit eigenem Subjekt (absoluter Gebrauch):', '<li>With its own subject (absolute construction):'),
    ],
    "13 Ergänzung des Verbs/03 Verben mit à.html": [
        ('<span class="de">The Commission shall take into account:</span>', '<span class="de">to expect</span>'),
    ],
    "13 Ergänzung des Verbs/05 Verben mit à und de.html": [
        ('<div class="de">For the purposes of this Regulation, the following definitions shall apply:</div>', '<div class="de">to agree on something</div>'),
    ],
    "14 Relativsätze/1 Relativsätze mit qui.html": [
        ('<p>In French, there is no distinction between der, die and das.</p>', '<p>French <span class="fr">qui</span> does not change for the gender or number of its antecedent; English usually translates it as “who,” “which,” or “that.”</p>'),
    ],
    "14 Relativsätze/2 Relativsätze mit que.html": [
        ('<p>Again, there is no difference between den, die and das in French.</p>', '<p>French <span class="fr">que</span> likewise does not change for gender or number; English commonly translates it as “whom,” “which,” or “that,” and may sometimes omit it.</p>'),
    ],
    "15 Bedingungssätze/1 Bedingungssätze mit si.html": [
        ('<p>This is the only way to ensure that the Commission\'s proposals are implemented in a manner that is consistent with the principle of subsidiarity.</p>', '<p>Here both the condition and its result are hypothetical: the condition is unlikely or cannot be fulfilled.</p>'),
    ],
    "18 Verneinung/03 Einschränkungen.html": [
        ('<p>Both . <span class="fr"><span class="tag-lemma">ne</span> ... <span class="tag-lemma">que</span></span> as well as <span class="fr tag-lemma">seulement</span> In this context, the Commission considers that there is a need for a clearer definition of what constraints can be used to express a constraint.</p>', '<p>Both <span class="fr"><span class="tag-lemma">ne</span> ... <span class="tag-lemma">que</span></span> and <span class="fr tag-lemma">seulement</span> can express a restriction meaning “only.”</p>'),
    ],
    "19 Inversion/1 Inversion mit Pronomen.html": [
        ('<p>If a verb ends in a vowel and <span class="fr">il</span>, <span class="fr">elle</span> or <span class="fr">on</span> The following is inserted for better pronunciation:</p>', '<p>If a verb ends in a vowel and is followed by <span class="fr">il</span>, <span class="fr">elle</span>, or <span class="fr">on</span>, insert <span class="fr">&#8209;t&#8209;</span> for pronunciation:</p>'),
        ('<h3>Question to the Council</h3>', '<h3>Questions</h3>'),
        ('<h3>Pushed sentences</h3>', '<h3>Reported speech and comments</h3>'),
        ('<p>The inversion is also used in direct speech or comments.</p>', '<p>Inversion also appears in reporting clauses and parenthetical comments.</p>'),
        ('<p>After <span class="fr">peut-être</span>, <span class="fr">sans doute</span> and the one who cries out, <span class="fr">combien</span> You need either an inversion or the word <span class="fr">que</span>:</p>', '<p>After <span class="fr">peut-être</span>, <span class="fr">sans doute</span>, and exclamative <span class="fr">combien</span>, French can use either inversion or a construction with <span class="fr">que</span>:</p>'),
        ('<li><span class="fr">à peine</span> (kaum)', '<li><span class="fr">à peine</span> (hardly; scarcely)'),
        ('<li><span class="fr">à plus forte raison</span> (erst recht)', '<li><span class="fr">à plus forte raison</span> (all the more reason)'),
        ('<li><span class="fr">du moins</span> (zumindest)', '<li><span class="fr">du moins</span> (at least)'),
        ('<li><span class="fr">(et) encore</span> (dennoch)', '<li><span class="fr">(et) encore</span> (even so; still)'),
        ('<li><span class="fr">encore moins</span> (noch weniger)', '<li><span class="fr">encore moins</span> (still less; even less)'),
        ('<li><span class="fr">rarement</span> (selten)', '<li><span class="fr">rarement</span> (rarely)'),
        ('<li><span class="fr">en vain</span> (where applicable)</li>', '<li><span class="fr">en vain</span> (in vain)</li>'),
    ],
    "19 Inversion/3 Inversion mit je.html": [
        ('<h3>Regular verbs on them</h3>', '<h3>Regular &#8209;er verbs</h3>'),
        ('<p>The <span class="fr">je</span>-form <a grammar="Die Verben auf -er"> of the regular verbs</a> has a special feature: the vowel at the end must be pronounced in the inversion.</p>', '<p>With regular <a grammar="Die Verben auf -er">&#8209;er verbs</a>, inversion of the <span class="fr">je</span> form requires the normally silent final <b>&#8209;e</b> to be pronounced; an accent marks this pronunciation.</p>'),
        ('<p class="attention">It is important for the debate: <span class="fr">je</span> is silent, so you can effectively <span class="ipa">\\pãsɛʒ\\</span> and <span class="ipa">\\parlɛʒ\\</span> He speaks.</p>', '<p class="attention">For pronunciation, the <b>&#8209;e</b> of <span class="fr">je</span> is silent, giving approximately <span class="ipa">\\pãsɛʒ\\</span> and <span class="ipa">\\parlɛʒ\\</span>.</p>'),
        ('<p>For verbs whose <span class="fr">je</span> form does not end, inversion is only possible with 10 very common verbs:</p>', '<p>For verbs whose <span class="fr">je</span> form does not end in <b>&#8209;e</b>, inversion is conventional with a small set of very common verbs:</p>'),
        ('<th>It \'s a verb .</th>', '<th>Verb</th>'),
        ('<th>Importance</th>', '<th>Meaning</th>'),
        ('<td>Going</td>', '<td>to go</td>'),
        ('<td><u>I \'m going to tell you something .</u></td>', '<td><u>ai-je</u></td>'),
        ('<td>must be</td>\n      <td><u>Two and a half years</u></td>', '<td>must; have to</td>\n      <td><u>dois-je</u></td>'),
        ('<td><u> this is</u></td>', '<td><u>dis-je</u></td>'),
        ('<td>sein</td>', '<td>to be</td>'),
        ('<td>Knowing</td>', '<td>to know</td>'),
        ('<td>Seeing</td>', '<td>to see</td>'),
        ('<p class="tip">Special feature: <span class="fr">puis</span> is a special form of <span class="fr">pouvoir</span>It is also important to note that the Commission has not yet adopted a proposal for a regulation. <span class="fr">je</span> is used.</p>', '<p class="tip">Special case: <span class="fr">puis</span> is a special form of <span class="fr">pouvoir</span> that survives today mainly in inversion with <span class="fr">je</span>.</p>'),
    ],
    "99 Vokabeln/13 Gesellschaft.html": [
        ('<span class="de">Proposal for a Council Directive</span>', '<span class="de">proposal; suggestion</span>'),
    ],
    "99 Vokabeln/14 Berufe.html": [
        ('<span class="de">President of the Council</span>', '<span class="de">president; chair</span>'),
        ('<span class="de">Members of the European Parliament</span>', '<span class="de">member of parliament; representative</span>'),
        ('<span class="de">President. - The next item is the report (Doc</span>', '<span class="de">president; chairwoman</span>'),
    ],
    "99 Vokabeln/24 Gegensätze.html": [
        ('<span class="de">Question from the Commission</span>', '<span class="de">question</span>'),
    ],
    "99 Vokabeln/27 Kommunikationsverben.html": [
        ('<span class="de">Proposal for a Council Regulation (EEC)</span>', '<span class="de">to suggest</span>'),
    ],
    "99 Vokabeln/28 Falsche Freunde.html": [
        ('<span class="de wrong left-x">Members of the Commission</span> (Parliament adopted the legislative resolution)', '<span class="de wrong left-x">colleague</span> (coworker)'),
        ('<span class="de wrong left-x">proper</span> For the purposes of this Regulation, the following definitions shall apply:', '<span class="de wrong left-x">proper</span> (appropriate; suitable)'),
        ('<span class="de wrong left-x">Council</span> (Advice)', '<span class="de wrong left-x">advice</span>'),
        ('<span class="de wrong left-x">agenda</span> (Applause from the Commission)', '<span class="de wrong left-x">agenda</span> (list of items to discuss)'),
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
        print(f"{rel}: reviewed-v10 replacements={changes}")
    return changes


def main() -> int:
    files = total = 0
    for path in sorted(Path("grammar").rglob("*.html")):
        count = apply(path)
        if count:
            files += 1
            total += count
    print(f"GRAMMAR REVIEWED REPAIRS V10: files={files} replacements={total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
