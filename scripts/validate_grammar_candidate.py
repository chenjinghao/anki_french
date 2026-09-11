#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from audit_grammar_english import baseline_paths, baseline_text, parse, suspicious

DEFAULT_BASE = '68e1d56f72ae0be70ea67fcc241fca372208b2e5'
KNOWN_BAD = (
    'specific article', 'particular article', 'certain article',
    'indeterminate article', 'divisional article', 'sex of the noun',
    'sex-related', 'male form', 'female form', 'verb trunk', 'the tribe',
    'possessive companions', 'indefinite companions', 'order number',
    'basic number', 'annexing', 'conjunctiv', 'apostrophed', 'prepositioned',
    'word type', 'sentence members', 'things and things', 'memorabilia',
    'stummem h', 'stummen h', '(bindung)', 'the friends',
    'presence) is a simple form of time', 'accumulator object',
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--baseline', default=DEFAULT_BASE)
    ap.add_argument('--report', default='grammar-candidate-qa.txt')
    args = ap.parse_args()

    paths = sorted(str(p) for p in Path('grammar').rglob('*.html'))
    basepaths = baseline_paths(args.baseline)
    errors: list[str] = []
    findings: list[str] = []
    if paths != basepaths:
        errors.append(f'HTML path set changed: candidate={len(paths)} baseline={len(basepaths)}')

    for path in sorted(set(paths) & set(basepaths)):
        now = parse(Path(path).read_text(encoding='utf-8'))
        before = parse(baseline_text(args.baseline, path))
        if Counter(now.attrs) != Counter(before.attrs):
            errors.append(f'{path}: compatibility attributes changed')
        if now.fr != before.fr:
            errors.append(f'{path}: French .fr text changed')
        if now.ipa != before.ipa:
            errors.append(f'{path}: IPA .ipa text changed')
        for text in now.visible:
            low = text.lower()
            if suspicious([text]) or any(term in low for term in KNOWN_BAD):
                findings.append(f'{path}: {text}')

    lines = [
        'GRAMMAR CANDIDATE QA',
        f'Baseline: {args.baseline}',
        f'Pages checked: {len(paths)}',
        f'Invariant errors: {len(errors)}',
        f'Quality findings: {len(findings)}',
        '',
    ]
    if errors:
        lines += ['INVARIANT ERRORS', *[f'- {x}' for x in errors], '']
    if findings:
        lines += ['QUALITY FINDINGS', *[f'- {x}' for x in findings], '']
    Path(args.report).write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'Pages={len(paths)} invariants={len(errors)} findings={len(findings)}')
    return 1 if errors or findings else 0


if __name__ == '__main__':
    raise SystemExit(main())
