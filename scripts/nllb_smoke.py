#!/usr/bin/env python3
"""Smoke-test NLLB German→English on known Marian failure cases."""
from __future__ import annotations

import os
from pathlib import Path

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

MODEL_NAME = os.environ.get("NLLB_MODEL", "facebook/nllb-200-distilled-600M")
SRC_LANG = "deu_Latn"
TGT_LANG = "eng_Latn"

SAMPLES = [
    (
        "Seine sprachliche Gewandtheit beeindruckt alle.",
        ["fluency", "impress"],
    ),
    (
        "Die scheinbare Leichtigkeit der Übung ist trügerisch.",
        ["apparent", "ease", "exercise"],
    ),
    (
        "Die Präposition de verschmilzt mit den bestimmten Artikeln le bzw. les zu einem Wort.",
        ["preposition", "definite", "article"],
    ),
    (
        "Der bestimmte Artikel",
        ["definite", "article"],
    ),
    (
        "Das Hotel zur Post befindet sich im Stadtzentrum.",
        ["hotel", "city"],
    ),
    (
        "Foutre ist ein vulgäres und umgangssprachliches Verb, das je nach Kontext verschiedene Bedeutungen haben kann.",
        ["vulgar", "verb", "context", "meaning"],
    ),
    (
        "Er drückt sich mit bemerkenswerter Leichtigkeit auf Französisch aus.",
        ["express", "ease", "French"],
    ),
    (
        "Wir suchen alle möglichen Erleichterungen für unsere Kunden.",
        ["customer"],
    ),
    (
        "Der bestimmte Artikel richtet sich nach dem Geschlecht und der Zahl des Substantivs.",
        ["definite", "article", "gender", "number", "noun"],
    ),
    (
        "Vor Substantiven, die mit einem Vokal oder einem stummen h beginnen, werden le und la zu l' verkürzt.",
        ["noun", "vowel", "silent", "shortened"],
    ),
]


def main() -> None:
    torch.set_num_threads(max(1, min(2, os.cpu_count() or 1)))
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, src_lang=SRC_LANG)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    model.eval()

    outputs: list[str] = []
    texts = [source for source, _ in SAMPLES]
    for start in range(0, len(texts), 4):
        batch = texts[start : start + 4]
        encoded = tokenizer(
            batch,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512,
        )
        with torch.inference_mode():
            generated = model.generate(
                **encoded,
                forced_bos_token_id=tokenizer.convert_tokens_to_ids(TGT_LANG),
                max_new_tokens=256,
                num_beams=4,
            )
        outputs.extend(tokenizer.batch_decode(generated, skip_special_tokens=True))

    lines = [f"MODEL: {MODEL_NAME}", ""]
    passed = 0
    for i, ((source, keywords), translated) in enumerate(zip(SAMPLES, outputs), 1):
        haystack = translated.lower()
        matched = [kw for kw in keywords if kw.lower() in haystack]
        ok = len(matched) >= max(1, len(keywords) - 1)
        passed += int(ok)
        lines.extend(
            [
                f"[{i}] {'PASS' if ok else 'REVIEW'}",
                f"DE: {source}",
                f"EN: {translated}",
                f"keywords: {', '.join(matched)} / {', '.join(keywords)}",
                "",
            ]
        )

    lines.append(f"Keyword smoke score: {passed}/{len(SAMPLES)}")
    report = "\n".join(lines) + "\n"
    print(report)
    Path("nllb-smoke.txt").write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
