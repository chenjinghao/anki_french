#!/usr/bin/env python3
"""Repair known v5 residuals without touching French text or HTML attributes."""
from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAG_SPLIT_RE = re.compile(r"(<[^>]+>)")
OPEN_TAG_RE = re.compile(r"^<\s*([A-Za-z][\w:-]*)\b")
CLOSE_TAG_RE = re.compile(r"^<\s*/\s*([A-Za-z][\w:-]*)\s*>")
CLASS_RE = re.compile(r"\bclass\s*=\s*(['\"])(.*?)\1", re.I)

EXACT = {
    "Jahr": "year",
    "keine": "none",
    "schon wieder": "again",
    "weder ... noch": "neither ... nor",
    "Verwendung": "Usage",
    "Gebrauch": "Usage",
    "Geschlecht": "Gender",
    "Bildung": "Formation",
    "Morgen": "Morning",
    "bedeutet": "means",
    "verwendet": "used",
    "verwendet.": "is used.",
    "verwendet:": "is used:",
    "benutzt": "used",
    "benutzt.": "is used.",
    "abgeleitet": "derived",
    "Angst": "fear",
    '"Angst"': '"fear"',
    "Adverbien": "adverbs",
    "Handlung": "action",
    "schon": "already",
    "gehen": "go",
    "wurde": "was",
    "verschiedene": "various",
    "Hilfsverbs": "auxiliary verb",
    "Alle": "All",
    "weder": "neither",
    "Monat.": "month.",
}

PHRASES = {
    "Man verwendet": "One uses",
    "Man benutzt": "One uses",
    "Man braucht": "One needs",
    "verwendet man": "one uses",
    "bedeutet bereits": "already means",
    "bedeutet eher": "rather means",
    "Es gibt jedoch einige subtile Unterschiede:": "However, there are some subtle differences:",
    "Ludwig XIV. wurde im Jahr 1638 geboren.": "Louis XIV was born in 1638.",
    "Victor Hugo wurde 1802 in Besançon geboren.": "Victor Hugo was born in Besançon in 1802.",
    "Ort des Geschehens": "scene of the action",
    "im vollen Sinne des Wortes": "in the full sense of the word",
    "im umfassenden Sinne.": "in the broad sense.",
    "verschiedene Bedeutungen haben kann.": "can have different meanings.",
    "Im Allgemeinen drückt es eine grobe, unhöfliche oder überaus lässige Handlung aus.": "In general, it expresses a crude, impolite, or extremely casual action.",
    "die alle aus seiner Grundbedeutung": "all of which derive from its basic meaning",
    "abgeleitet sind.": "are derived.",
    "Diese Grundbedeutung entwickelte sich in verschiedene Kontexte, z.B. als „Partisan“ oder „Verfechter“,": "This basic meaning developed into different contexts, e.g. as “partisan” or “advocate”,",
    "(= Irgendwann im Laufe des Vormittags → Zeitspanne)": "(= at some point during the morning → time span)",
    "des Substantivs": "of the noun",
    "Mitglied des Teams": "member of the team",
    "Adverbien des Ortes": "Adverbs of place",
    "Wechsel des Hilfsverbs": "Change of auxiliary verb",
    "des Hauptverbs": "of the main verb",
    "+ Indikativ bedeutet hier „feststellen“, „begreifen“.": "+ indicative here means “to establish”, “to understand”.",
    "des Hilfsverbs": "of the auxiliary verb",
    "oft anstelle des": "often instead of the",
    "Umschreibung des": "paraphrase of the",
    "Hab keine Angst": "Don't be afraid",
    "anstelle des": "instead of the",
    "im (Monat), im Jahr": "in (month), in (year)",
    "angekommen war.": "had arrived.",
    "Es gibt keine(s).": "There is none.",
    "Man musste gehen.": "One had to leave.",
    "Du verstehst schon,": "You know,",
    "Bereich verwendet.": "is used in this area.",
    ") gibt es folgende Bezeichnungen:": ") there are the following terms:",
    "letzten Monat": "last month",
    "Film des Jahres.": "film of the year.",
    "Er gibt": "He gives",
    "spazieren gehen": "go for a walk",
    "es gibt": "there is",
    "Lass uns jetzt gehen!": "Let's go now!",
    "gibt sich damit zufrieden": "is content with that",
    "Gibt genaue Zeitpunkte an:": "Indicates exact points in time:",
    "du ja fertig bist, kannst du gehen.": "since you're already finished, you can go.",
}

WORD_REPLACEMENTS = {
    "bedeutet": "means",
    "verwendet": "used",
    "benutzt": "used",
    "abgeleitet": "derived",
    "Adverbien": "adverbs",
    "Handlung": "action",
    "Hilfsverbs": "auxiliary verb",
}

PATH_REPLACEMENTS = {
    "cards/0098_ainsi.yml": [("wieder", "again")],
    "cards/1097_ramener.yml": [('"wieder mitbringen"', '"bring back"')],
    "cards/1339_soulever.yml": [
        ('"wieder aufrichten"', '"raise again"'),
        ('"feststellen"', '"determine"'),
    ],
    "cards/1890_foutre.yml": [
        ("Im Allgemeinen drückt es eine grobe, unhöfliche", "In general, it expresses a crude, impolite"),
        ("oder überaus lässige action aus.", "or extremely casual action."),
        ("Es kann so", "It can"),
        ("Oft wird es als Kraftausdruck", "It is often used as an expletive"),
        ("um Ärger,", "to express anger,"),
        ("Frust oder Gleichgültigkeit auszudrücken", "frustration, or indifference"),
        ("wie in der Redewendung", "as in the expression"),
        ("(es ist mir scheißegal).", "(I don't give a damn)."),
        ("In sexuellen Zusammenhängen meint", "In sexual contexts,"),
        ("und zählt daher zu den Schimpfwörtern im Französischen.", "and is therefore considered vulgar in French."),
    ],
    "cards/2320_répandre.yml": [("im allgemeineren Sinne:", "in the broader sense:")],
    "cards/2516_tenant.yml": [
        ("Diese Grundbedeutung", "This basic meaning"),
        ("entwickelte sich in verschiedene Kontexte, z.B. als „Partisan“ oder „Verfechter“,", "developed into different contexts, e.g. as “partisan” or “advocate”,"),
        ("der eine bestimmte Position „hält“.", "someone who “holds” a particular position."),
        ("Im Sport bezeichnet es den „Titelverteidiger“", "In sports it denotes the “title holder”"),
        ("oder „Pokalverteidiger“, der den Titel „hält“.", "or “cup holder”, who “holds” the title."),
        ("Die Redewendung", "The expression"),
        ("beschreibt die näheren Umstände einer Situation, also das,", "describes the circumstances of a situation, namely"),
        ("was man „hält“ und „endet“.", "what one “holds” and where it “ends”."),
        ("„in einem", "“in one"),
        ("Stück“ oder „zusammenhängend“, etwas, das als Ganzes „gehalten“ wird.", "piece” or “continuous”, something that is “held” as a whole."),
    ],
    "grammar/06 Adverbien/1 Die Formen von Adverbien.html": [
        ("noch", "still"),
        ("des Adjektivs", "of the adjective"),
    ],
    "grammar/07 Pronomen/01 Die verbundenen Personalpronomen.html": [("gehen.", "go.")],
    "grammar/07 Pronomen/13 Die Indefinitbegleiter.html": [
        ("Verschiedene", "Various"),
        ("ganz/alle", "whole/all"),
    ],
    "grammar/09 Verben/09 Reflexive Verben.html": [("im Monat Oktober", "in October")],
    "grammar/09 Verben/10 Unpersönliche Verben.html": [
        ("Es gibt", "There is"),
        ("noch Brot", "still bread"),
    ],
    "grammar/10 Zeitformen und Modi/12 Subjonctif.html": [
        ("Angst:", "fear:"),
        ("Aussagesatz + Indikativ im", "declarative sentence + indicative in the"),
    ],
    "grammar/10 Zeitformen und Modi/13 Subjonctif imparfait.html": [("gekommen war", "had come")],
    "grammar/13 Ergänzung des Verbs/03 Verben mit à.html": [("gibt sich", "is content")],
    "grammar/13 Ergänzung des Verbs/06 Verben mit pour.html": [("Er wurde", "He was")],
    "grammar/16 Präpositionen/2 Präpositionen der Zeit.html": [
        ("Thomas wurde", "Thomas was"),
        ("geboren.", "born."),
    ],
    "grammar/17 Konjunktionen/01 Beiordnende Konjunktionen.html": [("noch", "nor")],
    "grammar/20 Indirekte Rede/1 Die indirekte Rede.html": [("Indikativ", "indicative")],
    "grammar/20 Indirekte Rede/2 Der indirekte Aussagesatz.html": [
        ("angekommen.“", "arrived.”"),
        ("im folgenden Jahr", "the following year"),
    ],
    "grammar/21 Informelle Sprache/2 Informelle Pronomen.html": [("Wegfall des direkten Objekts", "omission of the direct object")],
    "grammar/21 Informelle Sprache/3 Informelle Fragen.html": [("Wann bist du angekommen?", "When did you arrive?")],
    "grammar/22 Zahlen und Zeitangaben/2 Ordnungszahlen.html": [("alle zwei Tage", "every two days")],
    "grammar/99 Vokabeln/02 Status und Beziehungen.html": [("Mitglied", "member")],
    "grammar/99 Vokabeln/03 Körper und Gesundheit.html": [("Angst, Beklemmung", "fear, anxiety")],
    "grammar/99 Vokabeln/04 Emotionen und Charakter.html": [("Angst, Beklemmung", "fear, anxiety")],
    "grammar/99 Vokabeln/13 Gesellschaft.html": [("Mitglied", "member")],
    "grammar/99 Vokabeln/25 Zeit.html": [("Monat", "month")],
    "grammar/99 Vokabeln/26 Bewegungsverben.html": [
        ("wieder abreisen", "leave again"),
        ("wieder vorbeigehen", "pass by again"),
    ],
    "grammar/99 Vokabeln/27 Kommunikationsverben.html": [("wieder sagen", "say again")],
    "grammar/99 Vokabeln/28 Falsche Freunde.html": [("(Ort/Lage)", "(place/location)")],
    "grammar/_/VerbenBringenMitnehmen.html": [('"wieder mitbringen"', '"bring back"')],
}


def apply_path_replacements(path: Path, text: str) -> str:
    rel = path.relative_to(ROOT).as_posix()
    for old, new in PATH_REPLACEMENTS.get(rel, []):
        text = text.replace(old, new)
    return text


def repair_visible_text(text: str) -> str:
    parts = TAG_SPLIT_RE.split(text)
    stack: list[bool] = []
    for i, part in enumerate(parts):
        if not part:
            continue
        if part.startswith("<"):
            if part.startswith(("<!--", "<!", "<?")):
                continue
            if CLOSE_TAG_RE.match(part):
                if stack:
                    stack.pop()
                continue
            m = OPEN_TAG_RE.match(part)
            if m and not part.rstrip().endswith("/>"):
                tag = m.group(1).lower()
                classes = ""
                cm = CLASS_RE.search(part)
                if cm:
                    classes = cm.group(2)
                protected = any(c in {"fr", "ipa"} for c in classes.split()) or tag == "code"
                stack.append((stack[-1] if stack else False) or protected)
            continue
        if stack and stack[-1]:
            continue

        stripped = html.unescape(part).strip()
        if not stripped:
            continue
        leading = part[: len(part) - len(part.lstrip())]
        trailing = part[len(part.rstrip()) :]
        value = part.strip()
        decoded = html.unescape(value)
        if decoded in EXACT:
            parts[i] = leading + EXACT[decoded] + trailing
            continue
        for old, new in PHRASES.items():
            value = value.replace(old, new)
        value = re.sub(r"(\(#\d+\))\s+bedeutet\b", r"\1 means", value)
        value = re.sub(r"\bbedeutet\s+allgemein\b", "generally means", value)
        for old, new in WORD_REPLACEMENTS.items():
            value = re.sub(rf"\b{re.escape(old)}\b", new, value)
        parts[i] = leading + value + trailing
    return "".join(parts)


def repair_card(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    in_examples = False
    example_line = 0
    note_start: int | None = None
    note_end: int | None = None
    in_note = False

    for i, raw in enumerate(lines):
        newline = "\n" if raw.endswith("\n") else ""
        line = raw[:-1] if newline else raw
        stripped = line.strip()

        if line and not line.startswith(" "):
            if in_note and not stripped.startswith("Notiz:") and note_end is None:
                note_end = i
            in_examples = stripped.startswith("Beispielsätze:")
            in_note = stripped.startswith("Notiz:")
            if in_note:
                note_start = i + 1
            example_line = 0

        if in_examples:
            if not stripped:
                example_line = 0
                continue
            if line.startswith("  "):
                if example_line % 2 == 1:
                    value = line.strip()
                    if "**" in value or value.count("*") % 2:
                        value = value.replace("*", "")
                        indent = line[: len(line) - len(line.lstrip())]
                        lines[i] = indent + value + newline
                example_line += 1

    if in_note and note_start is not None and note_end is None:
        note_end = len(lines)
    if note_start is not None and note_end is not None and note_start < note_end:
        payload = "".join(lines[note_start:note_end])
        repaired = repair_visible_text(payload)
        repaired = apply_path_replacements(path, repaired)
        replacement = repaired.splitlines(keepends=True)
        if len(replacement) == note_end - note_start:
            lines[note_start:note_end] = replacement

    path.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    for path in sorted((ROOT / "cards").glob("*.yml")):
        repair_card(path)
    for path in sorted((ROOT / "grammar").rglob("*.html")):
        text = path.read_text(encoding="utf-8")
        text = repair_visible_text(text)
        text = apply_path_replacements(path, text)
        path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
