#!/usr/bin/env python3
"""Select and validate a deterministic 500-card v6 scale pilot.

The scale pilot keeps every known regression card from v6_card_pilot, then fills
out the sample evenly across the 5,000-card rank range. Selection can be sharded
for parallel CPU translation. Validation reuses the revision-4 card gate and
adds compact, evenly distributed manual-review samples.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import v6_card_pilot as pilot
import v6_pilot as base

TARGET_CARDS = 500
MANUAL_SAMPLE_COUNT = 40


def cards_by_rank(root: Path) -> dict[int, Path]:
    out: dict[int, Path] = {}
    for path in sorted((root / "cards").glob("*.yml")):
        try:
            rank = int(path.name.split("_", 1)[0])
        except ValueError:
            continue
        out[rank] = path
    return out


def select_scale_cards(root: Path) -> list[str]:
    by_rank = cards_by_rank(root)
    if not by_rank:
        return []

    chosen = {rank for rank in pilot.CARD_RANKS if rank in by_rank}
    available = sorted(by_rank)
    remaining = TARGET_CARDS - len(chosen)
    if remaining > 0:
        # Fill the remaining slots at evenly spaced quantiles of the rank list.
        # Integer arithmetic makes the selection deterministic across runs.
        if remaining == 1:
            chosen.add(available[len(available) // 2])
        else:
            for i in range(remaining):
                idx = round(i * (len(available) - 1) / (remaining - 1))
                chosen.add(available[idx])

        # Quantile collisions with regression cards can leave us short. Fill the
        # exact target deterministically from low to high rank.
        if len(chosen) < TARGET_CARDS:
            for rank in available:
                chosen.add(rank)
                if len(chosen) >= TARGET_CARDS:
                    break

    chosen = set(sorted(chosen)[:TARGET_CARDS]) if len(chosen) > TARGET_CARDS else chosen
    return [by_rank[r].relative_to(root).as_posix() for r in sorted(chosen)]


def shard_paths(paths: list[str], shard: int, shards: int) -> list[str]:
    if shards < 1 or not 0 <= shard < shards:
        raise ValueError("invalid shard")
    return [path for i, path in enumerate(paths) if i % shards == shard]


def validate(root: Path, paths: list[str], report_path: Path) -> int:
    errors: list[str] = []
    regression_samples: list[str] = []
    for rel in paths:
        current = (root / rel).read_text(encoding="utf-8")
        original = base.git_show(rel)
        pilot.validate_card(rel, current, original, errors, regression_samples)

    manual_samples: list[str] = []
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
            manual_samples.append(f"## SCALE SAMPLE {rel}")
            for fr, en in pairs[:3]:
                manual_samples.append(f"FR: {fr}\nEN: {en}")

    lines = [
        "V6 CARD SCALE PILOT QUALITY REPORT",
        f"Cards checked: {len(paths)}",
        f"Errors: {len(errors)}",
        "",
    ]
    if errors:
        lines.append("ERRORS")
        lines.extend(f"- {error}" for error in errors)
        lines.append("")
    lines.append("KNOWN REGRESSION SAMPLES")
    lines.extend(regression_samples)
    lines.append("")
    lines.append("EVENLY DISTRIBUTED MANUAL-REVIEW SAMPLES")
    lines.extend(manual_samples)
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
        paths = select_scale_cards(root)
        if (args.shard is None) != (args.shards is None):
            parser.error("--shard and --shards must be supplied together")
        if args.shard is not None:
            paths = shard_paths(paths, args.shard, args.shards)
        Path(args.output).write_text("\n".join(paths) + "\n", encoding="utf-8")
        print(f"Selected {len(paths)} scale-pilot cards")
        return

    paths = [
        line.strip()
        for line in Path(args.paths_file).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    raise SystemExit(validate(root, paths, Path(args.report)))


if __name__ == "__main__":
    main()
