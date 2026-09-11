#!/usr/bin/env python3
"""Rank French/English card example pairs by cross-lingual semantic similarity.

This is a review aid, not a pass/fail gate. Low-similarity pairs are surfaced for
manual inspection because fluent false-friend translations can evade structural
and residue checks.
"""
from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

import v6_pilot as base

MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
TAG_RE = re.compile(r"<[^>]+>")


def clean(text: str) -> str:
    text = html.unescape(TAG_RE.sub(" ", text))
    text = text.replace("*", " ")
    return re.sub(r"\s+", " ", text).strip()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True)
    p.add_argument("--paths-file", required=True)
    p.add_argument("--report", required=True)
    p.add_argument("--limit", type=int, default=250)
    args = p.parse_args()

    root = Path(args.root)
    paths = [x.strip() for x in Path(args.paths_file).read_text(encoding="utf-8").splitlines() if x.strip()]
    rows: list[tuple[str, int, str, str]] = []
    for rel in paths:
        text = (root / rel).read_text(encoding="utf-8")
        try:
            pairs = base.example_pairs(text)
        except ValueError:
            continue
        for i, (fr, en) in enumerate(pairs, 1):
            cfr, cen = clean(fr), clean(en)
            if cfr and cen:
                rows.append((rel, i, fr, en))

    model = SentenceTransformer(MODEL)
    fr_emb = model.encode([clean(r[2]) for r in rows], batch_size=64, normalize_embeddings=True, show_progress_bar=True)
    en_emb = model.encode([clean(r[3]) for r in rows], batch_size=64, normalize_embeddings=True, show_progress_bar=True)
    scores = np.sum(fr_emb * en_emb, axis=1)
    order = np.argsort(scores)

    lines = [
        "V6 CROSS-LINGUAL SEMANTIC AUDIT",
        f"Cards: {len(paths)}",
        f"Example pairs: {len(rows)}",
        f"Model: {MODEL}",
        "NOTE: similarity is a review ranking only, not an automatic error threshold.",
        "",
        f"LOWEST {min(args.limit, len(rows))} PAIRS",
    ]
    for rank, idx in enumerate(order[: args.limit], 1):
        rel, pair_no, fr, en = rows[int(idx)]
        lines += [
            f"## {rank}. {rel} example {pair_no} | cosine={scores[int(idx)]:.4f}",
            f"FR: {fr}",
            f"EN: {en}",
            "",
        ]
    Path(args.report).write_text("\n".join(lines), encoding="utf-8")
    print(f"Audited {len(rows)} example pairs; report: {args.report}")


if __name__ == "__main__":
    main()
