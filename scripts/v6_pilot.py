#!/usr/bin/env python3
"""Select, validate, and bundle the NLLB v6 translation pilot."""
from __future__ import annotations

import argparse
import html
import re
import shutil
import subprocess
from pathlib import Path

import yaml

from translate_de_to_en_v6 import looks_german

KNOWN_CARD_RANKS = set(range(1, 31)) | {
    34, 44, 50, 100, 250, 500, 750, 1000, 1250, 1500, 1750, 1890,
    2000, 2250, 2500, 2750, 3000, 3250, 3500, 3624, 3750, 4000, 4250,
    4500, 4750, 5000,
}
KNOWN_GRAMMAR = {
    "grammar/03 Artikel/1 Der bestimmte Artikel.html",
    "grammar/10 Zeitformen und Modi/12 Subjonctif.html",
}
BAD_ENGLISH = re.compile(
    r"\b(?:linguistic attire|specific article|specific articles|particular article|"
    r"particular articles|certain article|certain articles|sex and number of the noun)\b|ZXQ",
    re.I,
)
TAG_RE = re.compile(r"<[^>]+>")
TAG_SPLIT_RE = re.compile(r"(<[^>]+>)")
OPEN_TAG_RE = re.compile(r"^<\s*([A-Za-z][\w:-]*)\b")
CLOSE_TAG_RE = re.compile(r"^<\s*/\s*([A-Za-z][\w:-]*)\s*>")
CLASS_RE = re.compile(r"\bclass\s*=\s*(['\"])(.*?)\1", re.I)


def git_show(path: str) -> str:
    proc = subprocess.run(
        ["git", "show", f"origin/main:{path}"],
        check=True,
        stdout=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    return proc.stdout


def select_paths(root: Path) -> list[str]:
    selected: set[str] = set()
    cards = sorted((root / "cards").glob("*.yml"))
    by_rank: dict[int, Path] = {}
    for path in cards:
        try:
            rank = int(path.name.split("_", 1)[0])
        except ValueError:
            continue
        by_rank[rank] = path
    for rank in KNOWN_CARD_RANKS:
        path = by_rank.get(rank)
        if path:
            selected.add(path.relative_to(root).as_posix())

    grammar_files = sorted((root / "grammar").rglob("*.html"))
    # One representative page from every grammar subdirectory.
    seen_dirs: set[Path] = set()
    for path in grammar_files:
        rel_parent = path.parent.relative_to(root)
        if rel_parent not in seen_dirs:
            selected.add(path.relative_to(root).as_posix())
            seen_dirs.add(rel_parent)
    # Also sample evenly across the grammar corpus.
    if grammar_files:
        step = max(1, len(grammar_files) // 12)
        for path in grammar_files[::step][:12]:
            selected.add(path.relative_to(root).as_posix())
    selected.update(p for p in KNOWN_GRAMMAR if (root / p).exists())
    return sorted(selected)


def extract_yaml_field(text: str, key: str) -> str:
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith(f"{key}:"):
            start = i
            break
    if start is None:
        return ""
    end = start + 1
    while end < len(lines):
        line = lines[end]
        if line and not line.startswith((" ", "\t")):
            break
        end += 1
    snippet = "\n".join(lines[start:end]) + "\n"
    try:
        value = yaml.safe_load(snippet).get(key, "")
    except Exception:
        return ""
    return value if isinstance(value, str) else ""


def example_pairs(text: str) -> list[tuple[str, str]]:
    value = extract_yaml_field(text, "Beispielsätze")
    nonempty = [line.strip() for line in value.splitlines() if line.strip()]
    if len(nonempty) % 2:
        raise ValueError(f"odd example line count: {len(nonempty)}")
    return [(nonempty[i], nonempty[i + 1]) for i in range(0, len(nonempty), 2)]


def definition(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("Definition:"):
            return line.split(":", 1)[1].strip()
    return ""


def note_text(text: str) -> str:
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith("Notiz:"):
            start = i
            break
    if start is None:
        return ""
    first = lines[start].split(":", 1)[1].strip()
    body = [first] if first and first not in {"|-", "|", "''", '""'} else []
    for line in lines[start + 1:]:
        if line and not line.startswith((" ", "\t")):
            break
        body.append(line.strip())
    return "\n".join(body)


def visible_nodes(markup: str) -> list[str]:
    parts = TAG_SPLIT_RE.split(markup)
    stack: list[tuple[str, bool]] = []
    out: list[str] = []
    for part in parts:
        if not part:
            continue
        if part.startswith("<"):
            if part.startswith("<!--") or part.startswith("<!") or part.startswith("<?"):
                continue
            if CLOSE_TAG_RE.match(part):
                if stack:
                    stack.pop()
                continue
            match = OPEN_TAG_RE.match(part)
            if match and not part.rstrip().endswith("/>"):
                tag = match.group(1).lower()
                classes = ""
                cm = CLASS_RE.search(part)
                if cm:
                    classes = cm.group(2)
                protected = any(c in {"fr", "ipa"} for c in classes.split()) or tag == "code"
                stack.append((tag, (stack[-1][1] if stack else False) or protected))
            continue
        if stack and stack[-1][1]:
            continue
        value = html.unescape(part).strip()
        if value:
            out.append(value)
    return out


def protected_fragments(markup: str, cls: str) -> list[str]:
    pattern = re.compile(
        rf"<([A-Za-z][\w:-]*)\b[^>]*class=(['\"])[^'\"]*\b{re.escape(cls)}\b[^'\"]*\2[^>]*>(.*?)</\1>",
        re.I | re.S,
    )
    return [m.group(3) for m in pattern.finditer(markup)]


def repeated_phrase(text: str) -> bool:
    words = re.findall(r"[A-Za-z']+", html.unescape(TAG_RE.sub(" ", text)).lower())
    if len(words) < 16:
        return False
    grams: dict[tuple[str, ...], int] = {}
    for i in range(len(words) - 3):
        gram = tuple(words[i:i + 4])
        grams[gram] = grams.get(gram, 0) + 1
    return max(grams.values(), default=0) >= 3


def validate_card(path: str, current: str, original: str, errors: list[str], samples: list[str]) -> None:
    try:
        cur_pairs = example_pairs(current)
        old_pairs = example_pairs(original)
    except ValueError as exc:
        errors.append(f"{path}: {exc}")
        return
    if len(cur_pairs) != len(old_pairs):
        errors.append(f"{path}: example pair count changed {len(old_pairs)} -> {len(cur_pairs)}")
        return
    for i, ((cur_fr, cur_en), (old_fr, old_de)) in enumerate(zip(cur_pairs, old_pairs), 1):
        if cur_fr != old_fr:
            errors.append(f"{path}: French example {i} changed")
        if cur_en == old_de:
            errors.append(f"{path}: example {i} unchanged from German")
        if looks_german(cur_en):
            errors.append(f"{path}: German remains in example {i}: {cur_en[:140]}")
        if BAD_ENGLISH.search(cur_en):
            errors.append(f"{path}: known bad English in example {i}: {cur_en[:140]}")
        if repeated_phrase(cur_en):
            errors.append(f"{path}: repetitive example {i}: {cur_en[:140]}")
    cur_def = definition(current)
    old_def = definition(original)
    if old_def and looks_german(old_def) and cur_def == old_def:
        errors.append(f"{path}: German definition unchanged")
    if cur_def and (looks_german(cur_def) or BAD_ENGLISH.search(cur_def)):
        errors.append(f"{path}: suspicious definition: {cur_def[:140]}")

    note = note_text(current)
    if note:
        for node in visible_nodes(note):
            if looks_german(node):
                errors.append(f"{path}: German remains in note: {node[:140]}")
            if BAD_ENGLISH.search(node) or repeated_phrase(node):
                errors.append(f"{path}: suspicious note English: {node[:140]}")

    if path.startswith(("cards/0002_", "cards/0022_", "cards/1890_", "cards/3624_")):
        samples.append(f"## {path}")
        for fr, en in cur_pairs[:6]:
            samples.append(f"FR: {fr}\nEN: {en}")
        if note:
            samples.append("NOTE: " + " ".join(visible_nodes(note))[:1000])


def validate_grammar(path: str, current: str, original: str, errors: list[str], samples: list[str]) -> None:
    if TAG_RE.findall(current) != TAG_RE.findall(original):
        errors.append(f"{path}: HTML tag/attribute sequence changed")
    for cls in ("fr", "ipa"):
        if protected_fragments(current, cls) != protected_fragments(original, cls):
            errors.append(f"{path}: .{cls} content changed")
    for node in visible_nodes(current):
        if looks_german(node):
            errors.append(f"{path}: German remains: {node[:160]}")
        if BAD_ENGLISH.search(node):
            errors.append(f"{path}: known bad English: {node[:160]}")
        if repeated_phrase(node):
            errors.append(f"{path}: repetitive English: {node[:160]}")
    if path in KNOWN_GRAMMAR:
        samples.append(f"## {path}")
        for node in visible_nodes(current)[:18]:
            samples.append(node[:600])


def validate(root: Path, paths: list[str], report_path: Path) -> int:
    errors: list[str] = []
    samples: list[str] = []
    for rel in paths:
        current = (root / rel).read_text(encoding="utf-8")
        original = git_show(rel)
        if rel.startswith("cards/"):
            validate_card(rel, current, original, errors, samples)
        elif rel.startswith("grammar/"):
            validate_grammar(rel, current, original, errors, samples)

    lines = [
        "V6 PILOT QUALITY REPORT",
        f"Files checked: {len(paths)}",
        f"Errors: {len(errors)}",
        "",
    ]
    if errors:
        lines.append("ERRORS")
        lines.extend(f"- {e}" for e in errors)
        lines.append("")
    lines.append("REPRESENTATIVE SAMPLES")
    lines.extend(samples)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(report_path.read_text(encoding="utf-8"))
    return 1 if errors else 0


def bundle(root: Path, paths: list[str], output: Path) -> None:
    if output.exists():
        shutil.rmtree(output)
    for rel in paths:
        dest = output / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / rel, dest)


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    select = sub.add_parser("select")
    select.add_argument("--root", default=".")
    select.add_argument("--output", required=True)
    check = sub.add_parser("validate")
    check.add_argument("--root", default=".")
    check.add_argument("--paths-file", required=True)
    check.add_argument("--report", required=True)
    pack = sub.add_parser("bundle")
    pack.add_argument("--root", default=".")
    pack.add_argument("--paths-file", required=True)
    pack.add_argument("--output", required=True)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if args.command == "select":
        paths = select_paths(root)
        Path(args.output).write_text("\n".join(paths) + "\n", encoding="utf-8")
        print(f"Selected {len(paths)} pilot files")
    else:
        paths = [line.strip() for line in Path(args.paths_file).read_text(encoding="utf-8").splitlines() if line.strip()]
        if args.command == "validate":
            raise SystemExit(validate(root, paths, Path(args.report)))
        bundle(root, paths, Path(args.output))
        print(f"Bundled {len(paths)} pilot files")


if __name__ == "__main__":
    main()
