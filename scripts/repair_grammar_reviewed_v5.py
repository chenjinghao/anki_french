#!/usr/bin/env python3
"""Deterministic reviewed repairs for the clean-source English grammar candidate.

These fixes are path-scoped and intentionally conservative. They repair stable model
output or earlier source-adaptation mistakes without touching French source text,
IPA, compatibility attributes, or legacy `.de` element counts.
"""
from __future__ import annotations

from pathlib import Path

REPLACEMENTS: dict[str, list[tuple[str, str]]] = {
    "08 Fragen/1 Die drei Frageformen.html": [
        (
            '<div class="section-title" data-topic="A1">The three forms of question</div>',
            '<div class="section-title" data-topic="A1">Three ways to form questions</div>',
        ),
        ('<h3>Question of intonation</h3>', '<h3>Intonation questions</h3>'),
        (
            '<p>The question of intonation maintains the position of the sentences of the statement, but is raised with increasing intonation, e.g.:</p>',
            '<p>An intonation question keeps normal statement word order and is spoken with rising intonation, for example:</p>',
        ),
        (
            '<h3><i>est-ce que</i>- Questions from the Commission</h3>',
            '<h3><i>est-ce que</i> questions</h3>',
        ),
        (
            '<p>An <span class="fr">est-ce que</span> question is formed by placing <span class="fr">est-ce que</span> before a statement; the statement word order otherwise stays unchanged. English has no direct equivalent of this fixed question marker. It is used in both spoken and written French.</p>',
            '<p>An <span class="fr">est-ce que</span> question is formed by placing <span class="fr">est-ce que</span> before a statement; the statement word order otherwise stays unchanged. The marker <span class="fr">est-ce que</span> has no direct equivalent in English. It is used in both spoken and written French.</p>',
        ),
        (
            '<p>Before vowel and <a grammar="Das h aspiré">silent h</a> will be <span class="fr">est-ce que</span> to <span class="fr">est-ce qu’</span>.</p>',
            '<p>Before a vowel or <a grammar="Das h aspiré">silent h</a>, <span class="fr">est-ce que</span> becomes <span class="fr">est-ce qu’</span>.</p>',
        ),
        ('<h3>The question of investment</h3>', '<h3>Inversion questions</h3>'),
        (
            '<p>The inversion question with and without a question word is formed as follows:</p>',
            '<p>Inversion questions, with or without a question word, are formed as follows:</p>',
        ),
        (
            '<p>In the case of investments, the following is stated: <a grammar="Die verbundenen Personalpronomen">Subject pronouns</a> between the verb and subject, a dash is inserted. Inversion questions, the question words are before the verb.</p>',
            '<p>In an inversion question, the <a grammar="Die verbundenen Personalpronomen">subject pronoun</a> follows the verb and is joined to it with a hyphen. A question word, when present, comes before the verb.</p>',
        ),
        (
            '<p class="highlight">In the third person singular <span class="fr">il</span>, <span class="fr">elle</span> or <span class="fr">on</span> occurs between verbs and subject pronouns <span class="fr">&#8209;t-</span>If the verb form is <span class="fr">&#8209;e</span> or <span class="fr">&#8209;a</span> It\'s over.</p>',
            '<p class="highlight">With third-person singular <span class="fr">il</span>, <span class="fr">elle</span>, or <span class="fr">on</span>, insert <span class="fr">&#8209;t-</span> between the verb and subject pronoun when the verb form ends in <span class="fr">&#8209;e</span> or <span class="fr">&#8209;a</span>.</p>',
        ),
        (
            '<p class="attention">If the subject of a sentence is a noun, the thing becomes more complicated because a noun cannot stand behind the verb.</p>',
            '<p class="attention">When the subject is a noun rather than a pronoun, French uses a special inversion pattern.</p>',
        ),
        (
            '<p>If you want to form the inversion question and a noun is a sentence object, the statement is retained and the corresponding subject pronoun is attached to the verb using a punctuation.</p>',
            '<p>Keep the noun subject in its normal position, then repeat it with the corresponding subject pronoun after the verb, joined by a hyphen.</p>',
        ),
    ],
}


def apply(path: Path) -> int:
    rel = str(path.relative_to("grammar"))
    rules = REPLACEMENTS.get(rel)
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
        print(f"{rel}: reviewed-v5 replacements={changes}")
    return changes


def main() -> int:
    files = total = 0
    for path in sorted(Path("grammar").rglob("*.html")):
        count = apply(path)
        if count:
            files += 1
            total += count
    print(f"GRAMMAR REVIEWED REPAIRS V5: files={files} replacements={total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
