#!/usr/bin/env python3
"""Revision-4 scale QA: semantic gate plus the expanded manual-100 review."""
from __future__ import annotations

import argparse
from pathlib import Path

import repair_v6_scale_manual100 as manual
import v6_card_pilot as pilot
import v6_pilot as base
import v6_scale_pilot as scale
import v6_scale_pilot_v3 as previous

MANUAL_SAMPLE_COUNT = 150


def manual_regressions(path: str, current: str, errors: list[str]) -> None:
    expected_def = manual.DEFINITIONS.get(path)
    if expected_def is not None and base.definition(current) != expected_def:
        errors.append(f"{path}: manual-100 definition regression: {base.definition(current)[:160]}")
    try:
        pairs = base.example_pairs(current)
    except ValueError:
        return
    pair_map = {fr: en for fr, en in pairs}
    for fr, expected in manual.EXAMPLES.items():
        if fr in pair_map and pair_map[fr] != expected:
            errors.append(f"{path}: manual-100 semantic regression for {fr[:90]} -> {pair_map[fr][:160]}")


def validate(root: Path, paths: list[str], report_path: Path) -> int:
    errors: list[str] = []
    regression_samples: list[str] = []
    for rel in paths:
        current = (root / rel).read_text(encoding="utf-8")
        original = base.git_show(rel)
        pilot.validate_card(rel, current, original, errors, regression_samples)
        previous.extra_checks(rel, current, errors)
        manual_regressions(rel, current, errors)

    review: list[str] = []
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
            review.append(f"## SCALE4 SAMPLE {rel}")
            review.append("Definition: " + base.definition(current))
            for fr, en in pairs[:5]:
                review.append(f"FR: {fr}\nEN: {en}")

    lines = [
        "V6 CARD SCALE PILOT QUALITY REPORT — MANUAL-100 REVISION 4",
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
    lines.append("EXPANDED 150-CARD MANUAL-REVIEW SAMPLES")
    lines.extend(review)
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
        print(f"Selected {len(paths)} scale4 cards")
        return
    paths = [line.strip() for line in Path(args.paths_file).read_text(encoding="utf-8").splitlines() if line.strip()]
    raise SystemExit(validate(root, paths, Path(args.report)))


if __name__ == "__main__":
    main()
