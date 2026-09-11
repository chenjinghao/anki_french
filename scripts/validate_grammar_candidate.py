#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

from audit_grammar_english import baseline_paths, baseline_text, parse, suspicious

DEFAULT_BASE = '68e1d56f72ae0be70ea67fcc241fca372208b2e5'
MAX_DE_SPAN_CHARS = 220
KNOWN_BAD = (
    'specific article', 'particular article', 'certain article',
    'indeterminate article', 'divisional article', 'sex of the noun',
    'sex-related', 'male form', 'female form', 'verb trunk', 'the tribe',
    'possessive companions', 'indefinite companions', 'order number',
    'basic number', 'annexing', 'conjunctiv', 'apostrophed', 'prepositioned',
    'word type', 'sentence members', 'things and things', 'memorabilia',
    'stummem h', 'stummen h', '(bindung)',
    'presence) is a simple form of time', 'accumulator object',
    'french prime minister', 'grundzahl', 'unbestimmte form',
    'teilungsartikel', 'aussprache beizubehalten', 'ausgesprochen (',
    'in german there', 'german neut', 'german plural', 'german language',
    'the debate on:', 'shall be binding',
    # High-signal untranslated German seen during full-candidate review.
    'sich ergeben', 'zurückgeben', 'anleihe', 'wortbildung', 'preisangabe',
    'fortbewegungsart', 'entfernung', 'materialangabe', 'urheberbezeichnung',
    'beweggrund', 'beachte:', 'wird für', 'gibt die', 'bezeichnet das',
    # Characteristic NLLB hallucinations for short glossary entries.
    'official journal of the european union', 'member states',
    'commission shall adopt', 'council of ministers', 'cold-rolled',
    'hot-rolled', 'standing committee',
)
GERMAN_WORD_RE = re.compile(
    r'\b(?:folgen|entspricht|erwartungen|zweck|mittel|ursache|verteilung|'
    r'anleihe|bindung|wortbildung|zurückgeben|räumen|herkunft|ausgangspunkt)\b',
    re.I,
)


class DeSpanCollector(HTMLParser):
    """Collect visible text for each individual legacy target span."""
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[dict[str, object]] = []
        self.spans: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        amap = {k: (v or '') for k, v in attrs}
        is_de = tag == 'span' and 'de' in set(amap.get('class', '').split())
        self.stack.append({'tag': tag, 'is_de': is_de, 'buf': []})

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        return

    def handle_data(self, data: str) -> None:
        for frame in self.stack:
            if frame['is_de']:
                frame['buf'].append(data)  # type: ignore[index, union-attr]

    def handle_endtag(self, tag: str) -> None:
        for idx in range(len(self.stack) - 1, -1, -1):
            if self.stack[idx]['tag'] != tag:
                continue
            closing = self.stack[idx:]
            del self.stack[idx:]
            for frame in closing:
                if frame['is_de']:
                    text = re.sub(r'\s+', ' ', ''.join(frame['buf'])).strip()  # type: ignore[arg-type]
                    self.spans.append(text)
            return


def de_spans(raw: str) -> list[str]:
    p = DeSpanCollector()
    p.feed(raw)
    p.close()
    return p.spans


def repetitive(text: str) -> bool:
    words = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ'-]+", text.lower())
    if len(words) < 30:
        return False
    unique = len(set(words))
    most = max(Counter(words).values(), default=0)
    return unique / len(words) < 0.22 or most / len(words) > 0.35


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
        now_raw = Path(path).read_text(encoding='utf-8')
        before_raw = baseline_text(args.baseline, path)
        now = parse(now_raw)
        before = parse(before_raw)
        if Counter(now.attrs) != Counter(before.attrs):
            errors.append(f'{path}: compatibility attributes changed')
        if now.fr != before.fr:
            errors.append(f'{path}: French .fr text changed')
        if now.ipa != before.ipa:
            errors.append(f'{path}: IPA .ipa text changed')

        for text in now.visible:
            low = text.lower()
            if suspicious([text]) or any(term in low for term in KNOWN_BAD) or GERMAN_WORD_RE.search(text):
                findings.append(f'{path}: {text}')

        candidate_spans = de_spans(now_raw)
        baseline_spans = de_spans(before_raw)
        if len(candidate_spans) != len(baseline_spans):
            errors.append(
                f'{path}: .de span count changed: candidate={len(candidate_spans)} baseline={len(baseline_spans)}'
            )
        for i, text in enumerate(candidate_spans):
            if len(text) > MAX_DE_SPAN_CHARS:
                findings.append(f'{path}: oversized .de span #{i + 1} ({len(text)} chars): {text}')
            if repetitive(text):
                findings.append(f'{path}: repetitive .de span #{i + 1}: {text}')
            if i < len(baseline_spans):
                old_len = len(baseline_spans[i])
                if old_len <= 100 and len(text) > max(MAX_DE_SPAN_CHARS, old_len * 4 + 40):
                    findings.append(
                        f'{path}: .de span #{i + 1} expanded suspiciously from {old_len} to {len(text)} chars: {text}'
                    )

    # Deduplicate repeated findings while preserving order.
    errors = list(dict.fromkeys(errors))
    findings = list(dict.fromkeys(findings))
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
