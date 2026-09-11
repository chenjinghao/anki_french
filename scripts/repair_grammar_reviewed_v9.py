#!/usr/bin/env python3
"""Comprehensive reviewed repair for the regular -er verb grammar page."""
from pathlib import Path

PATH = Path("grammar/09 Verben/02 Die Verben auf -er.html")

REPLACEMENTS = [
    ('<div class="section-title" data-topic="A1/A2">The verbs on them</div>', '<div class="section-title" data-topic="A1/A2">Verbs ending in &#8209;er</div>'),
    ('<p>The verbs on <b> of</b> form the largest group (about 90% of all verbs) and are all regular (except <span class="fr">aller</span>).</p>', '<p>Verbs ending in <b>&#8209;er</b> form the largest group (about 90% of French verbs) and are regular except for <span class="fr">aller</span>.</p>'),
    ('<p>The endings in the <a grammar="Présent">Presence</a> Noise <b>- e, -es, -e, -us, -ez, -ent</b>. Example of the verb <span class="fr tag-lemma">donner</span> (<span class="de">to give</span>):</p>', '<p>The <a grammar="Présent">present-tense</a> endings are <b>&#8209;e, &#8209;es, &#8209;e, &#8209;ons, &#8209;ez, &#8209;ent</b>. Here is <span class="fr tag-lemma">donner</span> (<span class="de">to give</span>) as an example:</p>'),
    ('<p>That \'s it . <i><a grammar="Participe passé">Participe passé</a></i> will be up <b>- it is</b> made up of:</p>', '<p>The <i><a grammar="Participe passé">participe passé</a></i> is formed with <b>&#8209;é</b>:</p>'),
    ('<span class="de">Speaking</span>', '<span class="de">to speak</span>'),
    ('<div class="de spoiler">I have <u>Speaking</u></div>', '<div class="de spoiler">I have <u>spoken</u></div>'),
    ('<p>Specific features of the spelling:</p>', '<p>Spelling changes:</p>'),
    ('<li>In the case of verbs on <b>- of which:</b> This will be <b>(c)</b> before <b>O</b> and <b>(a) for the purposes of this Regulation</b> to one <b>(c)</b>, to the <span class="ipa">\\s\\</span>- Keep the conversation going.</li>', '<li>For verbs ending in <b>&#8209;cer</b>, <b>c</b> becomes <b>ç</b> before <b>o</b> or <b>a</b> so that the <span class="ipa">\\s\\</span> sound is preserved.</li>'),
    ('<span class="de">Starting</span>', '<span class="de">to begin</span>'),
    ('<div class="de spoiler">Let\'s get started.</div>', '<div class="de spoiler">we begin</div>'),
    ('<li>In the case of verbs on <b>The Commission shall adopt implementing acts in accordance with the procedure referred to in paragraph 1 of this Article.</b> will be a <b>e</b> between <b>g</b> and <b>O</b>/<b>(a) for the purposes of this Regulation</b> Added to the <span class="ipa">\\ʒ\\</span>- to obtain a report.</li>', '<li>For verbs ending in <b>&#8209;ger</b>, an <b>e</b> is inserted between <b>g</b> and <b>o</b>/<b>a</b> so that the <span class="ipa">\\ʒ\\</span> sound is preserved.</li>'),
    ('<span class="de">eating</span>', '<span class="de">to eat</span>'),
    ('<div class="de spoiler">We \'re eating .</div>', '<div class="de spoiler">we eat</div>'),
    ('<li>In the case of verbs on <b>- Yes , sir .</b> This will be <b>y</b> Before a silent one <b>e</b> to one <b>(i) the</b>.</li>', '<li>For verbs ending in <b>&#8209;yer</b>, <b>y</b> changes to <b>i</b> before a silent <b>e</b>.</li>'),
    ('<li>In the case of verbs on <b>Other</b> and <b>- Other</b> the consonant is doubled before the end.</li>', '<li>With many verbs ending in <b>&#8209;eler</b> and <b>&#8209;eter</b>, the consonant before the ending is doubled in forms with a silent ending.</li>'),
    ('<span class="de">Calling</span>', '<span class="de">to call</span>'),
    ('<span class="de">Tossing</span>', '<span class="de">to throw</span>'),
    ('</span>But ... <span class="fr force-audio">nous appe', '</span>, but: <span class="fr force-audio">nous appe'),
    ('</span>But ... <span class="fr force-audio">nous je', '</span>, but: <span class="fr force-audio">nous je'),
    ('<div class="de spoiler">I\'m calling, but we\'re calling.</div>', '<div class="de spoiler">I call, but: we call</div>'),
    ('<div class="de spoiler">I\'m throwing, but we\'re throwing.</div>', '<div class="de spoiler">I throw, but: we throw</div>'),
    ('<li>In the case of verbs with <b>-e-</b> or <b>- It \'s ...</b> In the stem, the accent changes to <b>- It\'s all right.</b>.</li>', '<li>For verbs with <b>&#8209;e&#8209;</b> or <b>&#8209;é&#8209;</b> in the stem, the vowel often changes to <b>&#8209;è&#8209;</b> before a silent ending.</li>'),
    ('<span class="de">Get up</span>', '<span class="de">to get up</span>'),
    ('<span class="de">Repeat</span>', '<span class="de">to repeat</span>'),
    ('</span>But ... <span class="fr force-audio">nous nous l', '</span>, but: <span class="fr force-audio">nous nous l'),
    ('</span>But ... <span class="fr force-audio">vous rép', '</span>, but: <span class="fr force-audio">vous rép'),
    ('<div class="de spoiler">I\'m getting up, but we\'re getting up.</div>', '<div class="de spoiler">I get up, but: we get up</div>'),
    ('<div class="de spoiler">I repeat, but you repeat</div>', '<div class="de spoiler">I repeat, but: you repeat</div>'),
]


def main() -> int:
    if not PATH.exists():
        print("GRAMMAR REVIEWED REPAIRS V9: target page absent")
        return 0
    raw = PATH.read_text(encoding="utf-8")
    new = raw
    changes = 0
    for old, replacement in REPLACEMENTS:
        if old in new:
            new = new.replace(old, replacement)
            changes += 1
    if new != raw:
        PATH.write_text(new, encoding="utf-8")
    print(f"GRAMMAR REVIEWED REPAIRS V9: replacements={changes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
