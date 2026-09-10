#!/usr/bin/env python3
"""Lightweight quality helpers shared by v6 QA without model dependencies."""
from __future__ import annotations

import html
import re

GERMAN_HINTS = re.compile(
    r"\b(?:der|die|das|den|dem|ein|eine|einer|einem|einen|und|oder|aber|nicht|"
    r"mit|für|von|aus|zu|zur|zum|auf|bei|ist|sind|wird|werden|kann|können|"
    r"muss|müssen|hat|haben|als|wenn|dass|dies|diese|dieser|dieses|auch|nur|"
    r"sehr|mehr|weniger|vor|nach|ohne|über|unter|zwischen|seit|durch|gegen|"
    r"wegen|beim|vom|ins|ich|sie|wir|ihr|wer|wen|wem|wo|wie|mein|dein|sein|"
    r"unser|euer|präposition|artikel|substantiv|adjektiv|pronomen|satz|sätze|"
    r"gebrauch|verwendung|beispiel|beispiele|geschlecht|weiblich|männlich|"
    r"bildung|steht|keiner|kein|zehn|jahre|wort|sprache|zahl)\b|[äöüß]",
    re.IGNORECASE,
)
GERMAN_SUFFIX_RE = re.compile(
    r"\b[A-Za-zÄÖÜäöüß]+(?:keit|keiten|heit|heiten|lich|liche|lichen|licher|liches|"
    r"isch|ische|ischen|ischer|isches|erweise|schaft|schaften|ung|ungen)\b",
    re.IGNORECASE,
)


def looks_german(text: str) -> bool:
    value = html.unescape(text).strip()
    return bool(value and len(value) >= 2 and (GERMAN_HINTS.search(value) or GERMAN_SUFFIX_RE.search(value)))
