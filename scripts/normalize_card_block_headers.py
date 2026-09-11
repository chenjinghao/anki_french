#!/usr/bin/env python3
"""Normalize YAML block-scalar indentation indicators for the APKG source parser.

The card source occasionally uses headers such as ``|2-``. The custom APKG
parser intentionally only needs the semantic block/chomping behavior, because
all card block bodies are already indented in the repository. This build-only
normalization removes the explicit indentation digit without changing content.
"""
from __future__ import annotations

import re
from pathlib import Path

HEADER_RE = re.compile(r"^([^\n:#][^\n:]*:\s*)([|>])([1-9])([+-]?)\s*$", re.MULTILINE)


def main() -> int:
    changed = 0
    replacements = 0
    for path in sorted(Path("cards").glob("*.yml")):
        raw = path.read_text(encoding="utf-8")
        new, count = HEADER_RE.subn(lambda m: f"{m.group(1)}{m.group(2)}{m.group(4)}", raw)
        if count:
            path.write_text(new, encoding="utf-8")
            changed += 1
            replacements += count
    print(f"NORMALIZED CARD BLOCK HEADERS: files={changed} replacements={replacements}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
