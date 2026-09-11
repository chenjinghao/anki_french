#!/usr/bin/env python3
"""Audit learner-facing grammar HTML against the original German/source baseline.

The audit is deliberately conservative about compatibility: grammar page paths,
French/IPA text, and internal class/id/grammar/data-id attributes must remain stable.
Learner-facing text includes legacy `.de` spans because those classes are internal
compatibility hooks even though their displayed content should now be English.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable

DEFAULT_BASELINE = "03644402701805a1b8dd074cfcbb54ba7e7bf15e"
SENSITIVE_ATTRS = {"class", "id", "grammar", "data-id"}
SKIP_VISIBLE_TAGS = {"script", "style"}

# High-signal German fragments that should not remain in learner-facing English.
# Do not use single ambiguous words such as "hat", "in", "die", or "der" alone.
GERMAN_PATTERNS = [
    r"\b(?:der|die|das)\s+(?:bestimmte[nrms]?\s+|unbestimmte[nrms]?\s+)?(?:Artikel|Substantiv|Adjektiv|Adverb|Pronomen|Verb)\b",
    r"\b(?:bestimmte|unbestimmte|Teilungsartikel|Substantiv|Substantive|Adjektive|Adverbien|Pronomen|Präposition|Präpositionen)\b",
    r"\b(?:wird|werden|wurde|wurden)\s+(?:verwendet|gebildet|ausgesprochen|geschrieben|gesetzt|gebraucht)\b",
    r"\b(?:bedeutet|bezeichnet|entspricht|folgt|folgen|verwendet|gebildet|ausgesprochen|geschrieben|gebraucht)\b",
    r"\b(?:männlich|weiblich|männliche|weibliche|männlichen|weiblichen)\b",
    r"\b(?:stummem|stummen|Bindung|Endung|Endungen|Ausnahme|Ausnahmen|Beispiel|Beispiele|Aussprache|Schreibung)\b",
    r"\b(?:steht|stehen)\s+(?:vor|nach|im|in|am|beim)\b",
    r"\b(?:im|am|beim|vom|zum|zur|des|eines|einer)\s+(?:Französischen|Französisch|Substantivs|Verbs|Adjektivs|Satzes|Infinitivs)\b",
    r"\b(?:wenn|wird|werden|dann|immer|meistens|häufig|außer|sondern|obwohl|während)\b.*\b(?:ist|sind|steht|stehen|verwendet|gebraucht|gebildet|ausgesprochen)\b",
]
GERMAN_RE = re.compile("|".join(f"(?:{p})" for p in GERMAN_PATTERNS), re.I)

KNOWN_BAD = [
    "specific article",
    "particular article",
    "certain article",
    "indeterminate article",
    "liaison (bindung)",
    "stummem h",
    "stummen h",
    "elimination before",
    "elimination of the vowel",
    "the tribe of the",
    "plural presence",
    "annexing of a",
    "adapt to the noun in the sex",
    "conjunctiv",
]


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True)


def baseline_text(commit: str, path: str) -> str:
    return git("show", f"{commit}:{path}")


def baseline_paths(commit: str) -> list[str]:
    # Disable Git's C-style quoting so paths containing accents/umlauts remain
    # literal UTF-8 and can be compared with pathlib output. Without this, quoted
    # names end in `.html\"` and were silently omitted from the audit inventory.
    out = subprocess.check_output(
        ["git", "-c", "core.quotepath=false", "ls-tree", "-r", "--name-only", commit, "--", "grammar"],
        text=True,
    )
    return sorted(p for p in out.splitlines() if p.endswith(".html"))


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


class GrammarParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, set[str]]] = []
        self.visible: list[str] = []
        self.fr: list[str] = []
        self.ipa: list[str] = []
        self.attrs: list[tuple[str, str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        amap = {k: (v or "") for k, v in attrs}
        self.stack.append((tag, set(amap.get("class", "").split())))
        for key, value in attrs:
            if key in SENSITIVE_ATTRS:
                self.attrs.append((tag, key, value or ""))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for key, value in attrs:
            if key in SENSITIVE_ATTRS:
                self.attrs.append((tag, key, value or ""))

    def handle_endtag(self, tag: str) -> None:
        for idx in range(len(self.stack) - 1, -1, -1):
            if self.stack[idx][0] == tag:
                del self.stack[idx:]
                return

    def handle_data(self, data: str) -> None:
        text = norm(data)
        if not text:
            return
        tags = {tag for tag, _ in self.stack}
        if tags & SKIP_VISIBLE_TAGS:
            return
        classes = set().union(*(c for _, c in self.stack)) if self.stack else set()
        if "fr" in classes:
            self.fr.append(text)
            return
        if "ipa" in classes:
            self.ipa.append(text)
            return
        self.visible.append(text)


def parse(text: str) -> GrammarParser:
    p = GrammarParser()
    p.feed(text)
    p.close()
    return p


def suspicious(texts: Iterable[str]) -> list[str]:
    out: list[str] = []
    for t in texts:
        if GERMAN_RE.search(t):
            out.append(t)
            continue
        low = t.lower()
        if any(bad in low for bad in KNOWN_BAD):
            out.append(t)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", default=DEFAULT_BASELINE)
    ap.add_argument("--report", default="grammar-quality-audit.txt")
    ap.add_argument("--json", default="grammar-quality-audit.json")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()

    current = sorted(str(p) for p in Path("grammar").rglob("*.html"))
    old = baseline_paths(args.baseline)
    errors: list[str] = []
    if current != old:
        errors.append(f"grammar HTML path set changed: current={len(current)} baseline={len(old)}")

    records = []
    for path in sorted(set(current) | set(old)):
        if path not in current or path not in old:
            records.append({"path": path, "missing": True})
            continue
        now_raw = Path(path).read_text(encoding="utf-8")
        old_raw = baseline_text(args.baseline, path)
        now = parse(now_raw)
        before = parse(old_raw)

        page_errors: list[str] = []
        if Counter(now.attrs) != Counter(before.attrs):
            page_errors.append("compatibility attributes changed")
        if now.fr != before.fr:
            page_errors.append("French .fr text changed")
        if now.ipa != before.ipa:
            page_errors.append("IPA .ipa text changed")
        suspects = suspicious(now.visible)
        for msg in page_errors:
            errors.append(f"{path}: {msg}")

        records.append({
            "path": path,
            "visible_current": now.visible,
            "visible_german_baseline": before.visible,
            "french": now.fr,
            "ipa": now.ipa,
            "suspicious_current": suspects,
            "errors": page_errors,
        })

    report_lines = [
        "GRAMMAR ENGLISH QUALITY AUDIT",
        f"Baseline: {args.baseline}",
        f"HTML pages: {len(current)}",
        f"Invariant errors: {len(errors)}",
        f"Pages with suspicious learner-facing text: {sum(bool(r.get('suspicious_current')) for r in records)}",
        "",
    ]
    if errors:
        report_lines += ["INVARIANT ERRORS", *[f"- {e}" for e in errors], ""]

    for rec in records:
        report_lines.append("=" * 88)
        report_lines.append(rec["path"])
        if rec.get("missing"):
            report_lines.append("MISSING IN ONE SIDE")
            continue
        if rec["suspicious_current"]:
            report_lines.append("SUSPICIOUS CURRENT TEXT:")
            report_lines += [f"  ! {x}" for x in rec["suspicious_current"]]
        report_lines.append("CURRENT LEARNER-FACING TEXT:")
        report_lines += [f"  EN? {x}" for x in rec["visible_current"]]
        report_lines.append("BASELINE LEARNER-FACING TEXT:")
        report_lines += [f"  SRC {x}" for x in rec["visible_german_baseline"]]
        if rec["french"]:
            report_lines.append("PRESERVED FRENCH:")
            report_lines += [f"  FR  {x}" for x in rec["french"]]
        report_lines.append("")

    Path(args.report).write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    Path(args.json).write_text(json.dumps({
        "baseline": args.baseline,
        "page_count": len(current),
        "errors": errors,
        "records": records,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Grammar pages: {len(current)}")
    print(f"Invariant errors: {len(errors)}")
    print(f"Suspicious pages: {sum(bool(r.get('suspicious_current')) for r in records)}")
    if args.strict and errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
