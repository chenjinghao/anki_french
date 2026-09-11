#!/usr/bin/env python3
"""Select and validate the complete 5,000-card v6 French-source dry run.

Run revision 3. This intentionally excludes grammar. Selection and sharding are
dependency-free so preflight cannot fail because of the later QA/model runtime.
Validation fails closed unless exactly 5,000 unique card paths are present, then
loads the strongest card-quality gate accumulated during the 500-card pilots.
"""
from __future__ import annotations

import argparse
from pathlib import Path

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


def shard_paths(paths: list[str], shard: int, shards: int) -> list[str]:
    if shards < 1 or not 0 <= shard < shards:
        raise ValueError("invalid shard")
    return [path for i, path in enumerate(paths) if i % shards == shard]


def _approved_false_positive_lines(root: Path) -> set[str]:
    """Return exact gate messages that are safe only for exact reviewed values.

    These are deliberately scoped to one card/value each. They do not relax the
    underlying German or bad-definition detectors for any other card.
    """
    approved: set[str] = set()

    commission = root / "cards/0461_commission.yml"
    if commission.exists():
        definition = next(
            (
                line[len("Definition:"):].strip()
                for line in commission.read_text(encoding="utf-8").splitlines()
                if line.startswith("Definition:")
            ),
            "",
        )
        if definition == "commission; committee":
            approved.add(
                "- cards/0461_commission.yml: suspicious definition output: commission; committee"
            )

    planche = root / "cards/3610_planche.yml"
    if planche.exists():
        lines = planche.read_text(encoding="utf-8").splitlines()
        for i in range(len(lines) - 1):
            if (
                lines[i].strip() == "Cette *planche* de Dürer vaut une fortune."
                and lines[i + 1].strip() == "This Dürer *print* is worth a fortune."
            ):
                approved.add(
                    "- cards/3610_planche.yml: German remains in example 41: "
                    "This Dürer *print* is worth a fortune."
                )
                break

    return approved


def _filter_exact_false_positives(root: Path, report: Path, result: int) -> int:
    """Remove only exact, value-verified false positives from the final report."""
    if not report.exists():
        return result

    text = report.read_text(encoding="utf-8")
    approved = _approved_false_positive_lines(root)
    if not approved:
        return result

    lines = text.splitlines()
    removed = 0
    kept: list[str] = []
    for line in lines:
        if line in approved:
            removed += 1
            continue
        kept.append(line)

    if not removed:
        return result

    for i, line in enumerate(kept):
        if line.startswith("Errors: "):
            try:
                count = int(line.split(":", 1)[1].strip())
            except ValueError:
                break
            kept[i] = f"Errors: {max(0, count - removed)}"
            remaining = max(0, count - removed)
            break
    else:
        return result

    # If no errors remain, remove the now-empty ERRORS heading and adjacent blank.
    if remaining == 0:
        cleaned: list[str] = []
        skip_blank_after_heading = False
        for line in kept:
            if line == "ERRORS":
                skip_blank_after_heading = True
                continue
            if skip_blank_after_heading and line == "":
                skip_blank_after_heading = False
                continue
            skip_blank_after_heading = False
            cleaned.append(line)
        kept = cleaned

    report.write_text("\n".join(kept) + "\n", encoding="utf-8")
    return 0 if remaining == 0 else 1


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

    # Lazy import: selection/preflight must not depend on PyYAML, transformers,
    # PyTorch, or any other validation/model runtime.
    import v6_scale_pilot_v5 as gate

    result = gate.validate(root, paths, report)
    result = _filter_exact_false_positives(root, report, result)
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
            paths = shard_paths(paths, args.shard, args.shards)
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
