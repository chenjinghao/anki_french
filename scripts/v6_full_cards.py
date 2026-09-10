#!/usr/bin/env python3
"""Select and validate the complete 5,000-card v6 French-source dry run.

This intentionally excludes grammar. Selection is deterministic and shardable.
Validation fails closed unless exactly 5,000 unique card paths are present, then
reuses the strongest card-quality gate accumulated during the 500-card pilots.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import v6_scale_pilot as scale
import v6_scale_pilot_v5 as gate

EXPECTED_CARDS = 5000


def card_sort_key(path: Path) -> tuple[int, str]:
    try:
        rank = int(path.name.split("_", 1)[0])
    except ValueError:
        rank = 10**9
    return rank, path.name


def select_all_cards(root: Path) -> list[str]:
    paths = sorted((root / "cards").glob("*.yml"), key=card_sort_key)
    return [path.relative_to(root).as_posix() for path in paths]


def validate_full(root: Path, paths: list[str], report: Path) -> int:
    errors: list[str] = []
    if len(paths) != EXPECTED_CARDS:
        errors.append(f"expected {EXPECTED_CARDS} paths, got {len(paths)}")
    if len(set(paths)) != len(paths):
        errors.append("duplicate card paths found")

    on_disk = set(select_all_cards(root))
    supplied = set(paths)
    if supplied != on_disk:
        missing = sorted(on_disk - supplied)[:20]
        extra = sorted(supplied - on_disk)[:20]
        if missing:
            errors.append("missing combined cards: " + ", ".join(missing))
        if extra:
            errors.append("unexpected paths: " + ", ".join(extra))

    if errors:
        report.write_text(
            "V6 FULL 5000-CARD DRY RUN — PREFLIGHT FAILURE\n"
            + f"Cards supplied: {len(paths)}\n"
            + f"Errors: {len(errors)}\n\n"
            + "\n".join(f"- {e}" for e in errors)
            + "\n",
            encoding="utf-8",
        )
        for error in errors:
            print(error)
        return 1

    result = gate.validate(root, paths, report)
    # Make the scope unmistakable in the report produced by the reused gate.
    text = report.read_text(encoding="utf-8")
    report.write_text(
        "V6 FULL 5000-CARD FRENCH-SOURCE DRY RUN\n"
        + "Grammar excluded intentionally. No corpus commit is performed.\n\n"
        + text,
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    select = sub.add_parser("select")
    select.add_argument("--root", default=".")
    select.add_argument("--output", required=True)
    select.add_argument("--shard", type=int)
    select.add_argument("--shards", type=int)

    validate = sub.add_parser("validate")
    validate.add_argument("--root", required=True)
    validate.add_argument("--paths-file", required=True)
    validate.add_argument("--report", required=True)

    args = parser.parse_args()
    root = Path(args.root).resolve()

    if args.command == "select":
        paths = select_all_cards(root)
        if len(paths) != EXPECTED_CARDS:
            raise SystemExit(f"expected {EXPECTED_CARDS} card files, found {len(paths)}")
        if (args.shard is None) != (args.shards is None):
            parser.error("--shard and --shards must be supplied together")
        if args.shard is not None:
            paths = scale.shard_paths(paths, args.shard, args.shards)
        Path(args.output).write_text("\n".join(paths) + "\n", encoding="utf-8")
        print(f"Selected {len(paths)} full-run cards")
        return

    paths = [
        line.strip()
        for line in Path(args.paths_file).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    raise SystemExit(validate_full(root, paths, Path(args.report)))


if __name__ == "__main__":
    main()
