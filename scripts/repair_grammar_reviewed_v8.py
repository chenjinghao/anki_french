#!/usr/bin/env python3
"""Compatibility-safe cleanup after reviewed v6 repairs."""
from pathlib import Path

PATH = Path("grammar/18 Verneinung/01 Verneinungswörter.html")
OLD = 'plus a second negative word such as <span class="fr">pas</span>.'
NEW = 'plus a second negative word such as <i>pas</i>.'


def main() -> int:
    if not PATH.exists():
        print("GRAMMAR REVIEWED REPAIRS V8: target page absent")
        return 0
    raw = PATH.read_text(encoding="utf-8")
    if OLD not in raw:
        print("GRAMMAR REVIEWED REPAIRS V8: replacements=0")
        return 0
    PATH.write_text(raw.replace(OLD, NEW, 1), encoding="utf-8")
    print("GRAMMAR REVIEWED REPAIRS V8: replacements=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
