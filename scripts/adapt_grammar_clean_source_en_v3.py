#!/usr/bin/env python3
"""Invariant-safe English-learner adaptations for the clean German grammar source.

This wraps v2's reviewed replacements but corrects adaptations that changed
compatibility hooks. The deck's original .fr/.de elements and attributes are part of
the runtime contract, so English pedagogy may change text, never those hooks.
"""
from __future__ import annotations

from pathlib import Path

from adapt_grammar_clean_source_en_v2 import merged_replacements as _v2_replacements


DEMONSTRATIVE_OLD = (
    'Demonstrativbegleiter haben eine hinweisende Funktion: Sie bestimmen ein Substantiv näher. '
    'Im Deutschen gibt es zwei Demonstrativbegleiter: <span class="de">diese(&#8209;r/s)</span> '
    'und <span class="de">jene(&#8209;r/s)</span>. Das Französische hat nur einen, der sich in '
    'Geschlecht und Zahl dem begleiteten Substantiv anpasst.'
)
DEMONSTRATIVE_NEW = (
    'Demonstrative determiners point out or identify a noun. English distinguishes forms such as '
    '<span class="de">diese(&#8209;r/s)</span> and <span class="de">jene(&#8209;r/s)</span>. '
    'French uses one demonstrative-determiner paradigm that agrees with the noun in gender and '
    'number; distance can be clarified with the suffixes -ci and -là.'
)

QUESTION_OLD = (
    'Die Frage mit <span class="fr">est-ce que</span> wird gebildet, indem man '
    '<span class="fr">est-ce que</span> vor den Aussagesatz setzt. Die Stellung der einzelnen '
    'Satzglieder im Aussagesatz bleibt dabei unverändert. Die Frage mit '
    '<span class="fr">est-ce que</span> existiert im Deutschen nicht. Sie wird sowohl in der '
    'gesprochenen als auch in der geschriebenen Sprache verwendet.'
)
QUESTION_NEW = (
    'An <span class="fr">est-ce que</span> question is formed by placing '
    '<span class="fr">est-ce que</span> before a statement; the statement word order otherwise '
    'stays unchanged. The marker <span class="fr">est-ce que</span> has no direct equivalent '
    'in English. It is used in both spoken and written French.'
)

INDIRECT_OLD = (
    'Die indirekte Rede dient dazu, Gesagtes, Gedanken oder Wünsche wiederzugeben, ohne sie '
    'wörtlich zu zitieren. Im Französischen steht dabei, anders als im Deutschen, kein '
    'Konjunktiv, sondern der <b>Indikativ</b> oder der <b><a grammar="Conditionnel">Conditionnel</a></b>. '
    'Aussage- und Aufforderungssätze werden mit der Konjunktion <span class="fr">que</span> '
    '(<span class="de">dass</span>) eingeleitet, die nicht weggelassen werden darf.'
)
INDIRECT_NEW = (
    'Indirect speech reports words, thoughts, or wishes without quoting them directly. French '
    'normally uses the <b>indicative</b> or, where required by sequence of tenses or meaning, the '
    '<b><a grammar="Conditionnel">conditionnel</a></b>. Reported statements are introduced by '
    '<span class="fr">que</span> (<span class="de">dass</span>), which unlike English “that” '
    'cannot simply be omitted.'
)

FALSE_FRIENDS_EXTRA = [
    (
        '<h3>Falsche Freunde: Französisch–Deutsch</h3>',
        '<h3>False friends and meaning contrasts: French–English</h3>',
    ),
    (
        '<p>Diese Wörter sehen deutschen Wörtern sehr ähnlich, bedeuten aber etwas anderes.</p>',
        '<p>This table combines direct French–English false friends with useful meaning contrasts. '
        'Read the normal translation first, then use the contrast column to choose the French word '
        'for the other English meaning.</p>',
    ),
]


def merged_replacements() -> dict[str, list[tuple[str, str]]]:
    merged = _v2_replacements()

    def replace_new(path: str, old: str, new: str) -> None:
        rules = merged[path]
        for i, (src, _) in enumerate(rules):
            if src == old:
                rules[i] = (src, new)
                return
        raise RuntimeError(f'missing v2 adaptation anchor to override: {path}: {old[:100]!r}')

    replace_new('07 Pronomen/09 Die Demonstrativbegleiter.html', DEMONSTRATIVE_OLD, DEMONSTRATIVE_NEW)
    replace_new('08 Fragen/1 Die drei Frageformen.html', QUESTION_OLD, QUESTION_NEW)
    replace_new('20 Indirekte Rede/1 Die indirekte Rede.html', INDIRECT_OLD, INDIRECT_NEW)
    merged.setdefault('99 Vokabeln/28 Falsche Freunde.html', []).extend(FALSE_FRIENDS_EXTRA)
    return merged


def apply_page(path: Path, rules: list[tuple[str, str]]) -> int:
    raw = path.read_text(encoding='utf-8')
    changed = 0
    for old, new in rules:
        count = raw.count(old)
        if count != 1:
            rel = str(path.relative_to('grammar'))
            raise RuntimeError(
                f'{rel}: expected exactly one reviewed source fragment, found {count}: {old[:100]!r}'
            )
        raw = raw.replace(old, new, 1)
        changed += 1
    path.write_text(raw, encoding='utf-8')
    return changed


def apply_all() -> int:
    rules_by_path = merged_replacements()
    total = 0
    for rel in sorted(rules_by_path):
        path = Path('grammar') / rel
        if not path.exists():
            raise RuntimeError(f'missing grammar page for reviewed source adaptation: {rel}')
        changed = apply_page(path, rules_by_path[rel])
        total += changed
        print(f'{rel}: English-learner source adaptations v3={changed}')
    print(f'ENGLISH-LEARNER CLEAN-SOURCE ADAPTATIONS V3: pages={len(rules_by_path)} replacements={total}')
    return total


def main() -> int:
    apply_all()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
