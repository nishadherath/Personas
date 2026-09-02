#!/usr/bin/env python3
"""Build ENGINEERING_PERSONA.<class>.md and ENGINEERING_PERSONA_LANGUAGES/<lang>.<class>.md
from source/core.source.md and source/languages.source.md.

Usage: python3 build_persona.py [--dist DIR]

Do not edit the generated files by hand. Edit the two source files and rerun this script.
"""
from __future__ import annotations
import argparse
import datetime
import re
import sys
from pathlib import Path

CLASSES = ("haiku", "sonnet", "opus", "fable")
TAG_RANK = {"all": 0, "sonnet+": 1, "opus+": 2}
CLASS_CEILING = {"haiku": "all", "sonnet": "sonnet+", "opus": "opus+", "fable": "opus+"}
# opus and fable share a ceiling, so their body content is identical by design: no tag
# in core.source.md or languages.source.md currently marks fable-exclusive material.
# Each still gets its own file and header so an agent's harness can load by its own
# class name. If genuinely fable-only content emerges, add a "fable+" tier above
# "opus+" in TAG_RANK and CLASS_CEILING rather than duplicating this file by hand.
TAG_RE = re.compile(r"\s*`\[(all|sonnet\+|opus\+)\]`")

CLASS_LABEL = {
    "haiku": "Haiku",
    "sonnet": "Sonnet",
    "opus": "Opus",
    "fable": "Fable",
}

TOKENS_PER_WORD = 1.3  # rough calibration factor for the report only; not used in any shipped file


def tag_included(tag: str, target_class: str) -> bool:
    return TAG_RANK[tag] <= TAG_RANK[CLASS_CEILING[target_class]]


def split_core(source_text: str) -> dict[str, str]:
    """Return {class: assembled_markdown} for the core persona document."""
    lines = source_text.splitlines()
    current_h2_tag = "all"
    current_h3_tag = None
    buffers: dict[str, list[str]] = {c: [] for c in CLASSES}

    for raw in lines:
        is_h3 = raw.startswith("### ")
        is_h2 = raw.startswith("## ") and not is_h3
        is_h1 = raw.startswith("# ") and not raw.startswith("## ")

        if is_h1:
            current_h2_tag = "all"
            current_h3_tag = None
            active = "all"
            clean = TAG_RE.sub("", raw)
        elif is_h2:
            m = TAG_RE.search(raw)
            current_h2_tag = m.group(1) if m else "all"
            current_h3_tag = None
            active = current_h2_tag
            clean = TAG_RE.sub("", raw)
        elif is_h3:
            m = TAG_RE.search(raw)
            current_h3_tag = m.group(1) if m else None
            active = current_h3_tag or current_h2_tag
            clean = TAG_RE.sub("", raw)
        else:
            active = current_h3_tag or current_h2_tag
            clean = raw

        for cls in CLASSES:
            if tag_included(active, cls):
                buffers[cls].append(clean)

    return {cls: collapse_blank_runs("\n".join(lines_)) for cls, lines_ in buffers.items()}


def collapse_blank_runs(text: str) -> str:
    """Collapse 3+ consecutive blank lines down to 1, left over from omitted sections."""
    return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"


LABEL_RE = re.compile(r"^\*\*([A-Za-z ]+)\.\*\*\s?(.*)$")


def parse_languages(source_text: str) -> list[dict]:
    """Parse languages.source.md into a list of {slug, title, sections: {label: text}}."""
    blocks = re.split(r"\n---\n", source_text)
    profiles = []
    for block in blocks:
        slug_m = re.search(r"^## SLUG:\s*(\S+)", block, re.MULTILINE)
        title_m = re.search(r"^## TITLE:\s*(.+)$", block, re.MULTILINE)
        if not slug_m or not title_m:
            continue
        slug = slug_m.group(1).strip()
        title = title_m.group(1).strip()

        sections: dict[str, list[str]] = {}
        current_label = None
        for line in block.splitlines():
            if line.startswith("## SLUG:") or line.startswith("## TITLE:"):
                continue
            m = LABEL_RE.match(line)
            if m:
                current_label = m.group(1).strip()
                sections[current_label] = [m.group(2)] if m.group(2) else []
            elif current_label is not None:
                sections[current_label].append(line)

        cleaned = {
            label: "\n".join(content_lines).strip()
            for label, content_lines in sections.items()
        }
        profiles.append({"slug": slug, "title": title, "sections": cleaned})
    return profiles


HAIKU_ORDER = ["For", "Checklist", "Hazard"]
FULL_BASE_ORDER = ["For", "Illegal states", "Structure", "Errors", "Tooling", "Hazard"]


def assemble_language_file(profile: dict, cls: str) -> str:
    sections = profile["sections"]
    if cls == "haiku":
        order = HAIKU_ORDER
    elif cls == "sonnet":
        order = FULL_BASE_ORDER
    else:
        order = FULL_BASE_ORDER + ["Judgment"]

    parts = []
    for label in order:
        content = sections.get(label)
        if not content:
            continue
        parts.append(f"**{label}.** {content}" if "\n" not in content else f"**{label}.**\n{content}")
    return "\n\n".join(parts) + "\n"


def core_header(cls: str) -> str:
    label = CLASS_LABEL[cls]
    today = datetime.date.today().isoformat()
    return (
        f"<!-- GENERATED FILE. Do not edit by hand.\n"
        f"     Source: source/core.source.md\n"
        f"     Class:  {label}\n"
        f"     Built:  {today} by build_persona.py\n"
        f"     Edit the source and rerun the build to change this file. -->\n\n"
        f"**This is the {label}-class edition of the engineering persona.** "
        f"Pair it with exactly one file per language in play from `ENGINEERING_PERSONA_LANGUAGES/` "
        f"in the same class (`.{cls}.md`). See the repository README for the full loading matrix "
        f"and how to regenerate these files.\n\n"
        f"---\n\n"
    )


def language_header(profile: dict, cls: str) -> str:
    label = CLASS_LABEL[cls]
    today = datetime.date.today().isoformat()
    return (
        f"<!-- GENERATED FILE. Do not edit by hand.\n"
        f"     Source: source/languages.source.md ({profile['slug']})\n"
        f"     Class:  {label}\n"
        f"     Built:  {today} by build_persona.py\n"
        f"     Edit the source and rerun the build to change this file. -->\n\n"
        f"# {profile['title']}: {label}-class profile\n\n"
        f"Language profile for the engineering persona. Load alongside "
        f"`ENGINEERING_PERSONA.{cls}.md`.\n\n"
        f"---\n\n"
    )


def word_count(text: str) -> int:
    return len(text.split())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dist", default="dist", help="output directory")
    ap.add_argument("--source-dir", default="source", help="source directory")
    args = ap.parse_args()

    root = Path(__file__).parent
    source_dir = root / args.source_dir
    dist_dir = root / args.dist
    lang_dir = dist_dir / "ENGINEERING_PERSONA_LANGUAGES"
    lang_dir.mkdir(parents=True, exist_ok=True)

    core_source_path = source_dir / "core.source.md"
    languages_source_path = source_dir / "languages.source.md"

    if not core_source_path.exists():
        print(f"error: missing {core_source_path}", file=sys.stderr)
        return 1
    if not languages_source_path.exists():
        print(f"error: missing {languages_source_path}", file=sys.stderr)
        return 1

    core_text = core_source_path.read_text(encoding="utf-8")
    lang_text = languages_source_path.read_text(encoding="utf-8")

    core_by_class = split_core(core_text)
    profiles = parse_languages(lang_text)

    report_lines = []
    report_lines.append(f"{'file':45s} {'words':>8s} {'~tokens':>8s}")

    for cls in CLASSES:
        out_path = dist_dir / f"ENGINEERING_PERSONA.{cls}.md"
        body = core_header(cls) + core_by_class[cls]
        out_path.write_text(body, encoding="utf-8")
        wc = word_count(body)
        report_lines.append(f"{out_path.name:45s} {wc:8d} {round(wc * TOKENS_PER_WORD):8d}")

    for profile in profiles:
        for cls in CLASSES:
            out_path = lang_dir / f"{profile['slug']}.{cls}.md"
            body = language_header(profile, cls) + assemble_language_file(profile, cls)
            out_path.write_text(body, encoding="utf-8")
            wc = word_count(body)
            report_lines.append(f"{('LANGUAGES/' + out_path.name):45s} {wc:8d} {round(wc * TOKENS_PER_WORD):8d}")

    report_path = dist_dir / "BUILD_REPORT.txt"
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"Built {len(CLASSES)} core files and {len(profiles) * len(CLASSES)} language files into {dist_dir}")
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
