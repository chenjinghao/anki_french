#!/usr/bin/env python3
"""Revision-3 QA for the French-source 500-card pilot.

This gate keeps the structural/residual-German checks from the card pilot, adds
all source-keyed reviewed regressions, and checks severe dropped clauses. It does
not require English emphasis markers to mirror French markers: idiomatic English
can express the same target without a one-to-one highlighted token.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import repair_v6_scale as r1
import repair_v6_scale_extra as r2
import v6_card_pilot as pilot
import v6_pilot as base
import v6_scale_pilot as scale

MANUAL_SAMPLE_COUNT = 100
BAD_DEFINITION = re.compile(
    r"\b(?:commission|member states?|standing committee|official journal|"
    r"manufacture of foodstuffs|cold-rolled|what are you(?: doing)?|"
    r"this is the case in the united kingdom)\b",
    re.I,
)


def sentence_marks(text: str) -> int:
    return len(re.findall(r'[.!?](?:["”»)]*)?(?=\s|$)', text))


def compact_len(text: str) -> int:
    return len(re.sub(r'[^A-Za-zÀ-ÖØ-öø-ÿ0-9]+', '', text))


def definition_continuations(text: str) -> list[str]:
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if line.startswith("Definition:")), None)
    if start is None:
        return []
    out: list[str] = []
    i = start + 1
    while i < len(lines):
        line = lines[i]
        if line.strip() and not line.startswith((" ", "\t")):
            break
        if line.startswith((" ", "\t")) and line.strip():
            out.append(line.strip())
        i += 1
    return out


def extra_checks(path: str, current: str, errors: list[str]) -> None:
    cur_def = base.definition(current)
    continuation = definition_continuations(current)
    if continuation:
        errors.append(f"{path}: malformed/leftover Definition continuation: {continuation[:2]}")
    if cur_def and (len(cur_def) > 100 or BAD_DEFINITION.search(cur_def)):
        errors.append(f"{path}: suspicious definition output: {cur_def[:160]}")

    expected_def = r2.DEFINITIONS.get(path, r1.DEFINITION_REVIEWED.get(path))
    if expected_def is not None and cur_def != expected_def:
        errors.append(f"{path}: reviewed definition regression: {cur_def[:160]}")

    try:
        pairs = base.example_pairs(current)
    except ValueError:
        return
    pair_map = {fr: en for fr, en in pairs}

    for mapping in (r1.REVIEWED, r2.EXAMPLES):
        for fr, expected in mapping.items():
            if fr in pair_map and pair_map[fr] != expected:
                errors.append(f"{path}: reviewed semantic regression for {fr[:90]} -> {pair_map[fr][:160]}")

    for i, (fr, en) in enumerate(pairs, 1):
        # Formatting integrity: a translation may omit/reposition emphasis, but it
        # must never contain broken unmatched markup.
        if en.count("*") % 2:
            errors.append(f"{path}: unmatched emphasis marker in example {i}: {en[:160]}")

        # Severe completeness signal only. This intentionally avoids requiring a
        # one-to-one sentence count because English can naturally combine clauses.
        fr_marks = sentence_marks(fr)
        en_marks = sentence_marks(en)
        ratio = compact_len(en) / max(1, compact_len(fr))
        if fr_marks >= 2 and en_marks < fr_marks and ratio < 0.50:
            errors.append(f"{path}: likely dropped clause in example {i}: {fr[:100]} -> {en[:160]}")


def validate(root: Path, paths: list[str], report_path: Path) -> int:
    errors: list[str] = []
    regression_samples: list[str] = []
    for rel in paths:
        current = (root / rel).read_text(encoding="utf-8")
        original = base.git_show(rel)
        pilot.validate_card(rel, current, original, errors, regression_samples)
        extra_checks(rel, current, errors)

    samples: list[str] = []
    if paths:
        count = min(MANUAL_SAMPLE_COUNT, len(paths))
        indices = sorted({round(i * (len(paths) - 1) / max(1, count - 1)) for i in range(count)})
        for idx in indices:
            rel = paths[idx]
            current = (root / rel).read_text(encoding="utf-8")
            try:
                pairs = base.example_pairs(current)
            except ValueError:
                continue
            samples.append(f"## SCALE3 SAMPLE {rel}")
            samples.append("Definition: " + base.definition(current))
            for fr, en in pairs[:5]:
                samples.append(f"FR: {fr}\nEN: {en}")

    lines = [
        "V6 CARD SCALE PILOT QUALITY REPORT — SEMANTIC REVISION 3",
        f"Cards checked: {len(paths)}",
        f"Errors: {len(errors)}",
        "",
    ]
    if errors:
        lines.append("ERRORS")
        lines.extend(f"- {e}" for e in errors)
        lines.append("")
    lines.append("REGRESSION SAMPLES")
    lines.extend(regression_samples)
    lines.append("")
    lines.append("EVENLY DISTRIBUTED MANUAL-REVIEW SAMPLES")
    lines.extend(samples)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Cards checked: {len(paths)}; errors: {len(errors)}")
    print(f"Report: {report_path}")
    return 1 if errors else 0


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    select = sub.add_parser("select")
    select.add_argument("--root", default=".")
    select.add_argument("--output", required=True)
    select.add_argument("--shard", type=int)
    select.add_argument("--shards", type=int)
    check = sub.add_parser("validate")
    check.add_argument("--root", default=".")
    check.add_argument("--paths-file", required=True)
    check.add_argument("--report", required=True)
    args = parser.parse_args()
    root = Path(args.root).resolve()

    if args.command == "select":
        paths = scale.select_scale_cards(root)
        if (args.shard is None) != (args.shards is None):
            parser.error("--shard and --shards must be supplied together")
        if args.shard is not None:
            paths = scale.shard_paths(paths, args.shard, args.shards)
        Path(args.output).write_text("\n".join(paths) + "\n", encoding="utf-8")
        print(f"Selected {len(paths)} scale3 cards")
        return

    paths = [line.strip() for line in Path(args.paths_file).read_text(encoding="utf-8").splitlines() if line.strip()]
    raise SystemExit(validate(root, paths, Path(args.report)))


if __name__ == "__main__":
    main()
