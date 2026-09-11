#!/usr/bin/env python3
"""Translate one clean-source grammar shard with resilient prose and target passes."""
from __future__ import annotations

import argparse
from pathlib import Path

from translate_cards_fr_en_v6 import CardTranslator
from translate_grammar_examples_hybrid_v4 import card_lemma_memory, translate_page as translate_examples
from translate_grammar_prose_de_en_v3 import translate_page as translate_prose


def page_paths(shard: int, shards: int) -> list[Path]:
    paths = sorted(Path("grammar").rglob("*.html"))
    return [path for i, path in enumerate(paths) if i % shards == shard]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--shards", type=int, default=1)
    ap.add_argument("--batch-size", type=int, default=16)
    args = ap.parse_args()
    if not (0 <= args.shard < args.shards):
        raise SystemExit("invalid shard")

    translator = CardTranslator(Path("."), batch_size=args.batch_size)
    memory = card_lemma_memory()
    pages = page_paths(args.shard, args.shards)
    prose_blocks = prose_changes = prose_unresolved = 0
    example_pairs = example_changes = sensitive = wrong = long_span = 0

    for path in pages:
        pb, pc, pu = translate_prose(path, translator.de)
        ep, ec, es, ew, el = translate_examples(path, translator, memory)
        prose_blocks += pb
        prose_changes += pc
        prose_unresolved += pu
        example_pairs += ep
        example_changes += ec
        sensitive += es
        wrong += ew
        long_span += el
        print(
            f"{path}: prose_blocks={pb} prose_changes={pc} prose_unresolved={pu} "
            f"example_pairs={ep} example_changes={ec} skipped_sensitive={es} "
            f"skipped_wrong={ew} skipped_long_span={el}"
        )

    print(
        f"GRAMMAR CLEAN-SOURCE V2 SHARD {args.shard}/{args.shards}: pages={len(pages)} "
        f"prose_blocks={prose_blocks} prose_changes={prose_changes} "
        f"prose_unresolved={prose_unresolved} example_pairs={example_pairs} "
        f"example_changes={example_changes} skipped_sensitive={sensitive} "
        f"skipped_wrong={wrong} skipped_long_span={long_span} lemma_memory={len(memory)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
