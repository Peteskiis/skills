#!/usr/bin/env python3
"""Deterministic publish checker for the news agent's story file.

This is the SINGLE SOURCE OF TRUTH for "is this story publishable". It runs
two ways, byte-identically:
  1. seeded into the run's VM and invoked by the agent's `shell` tool loop
     (`python3 check_story.py --sources N story.md`), and
  2. re-executed by `submit_story` as the publish gate, piped via stdin
     (`python3 - --sources N story.md <<'CHECKER_EOF' ... CHECKER_EOF`).

Constraints that keep both invocation shapes working (enforced by
tests/check_story_fixtures.rs):
  - stdlib only (sys, re, argparse) — the `development` VM template installs
    python3 but no pip packages.
  - no `__file__` dependence — must run when the source arrives on stdin.
  - NO line in this file may equal `CHECKER_EOF` (it terminates the M3
    heredoc) and NO line may start with `*** ` (it would corrupt the codex
    `*** Add File` seed envelope).

Exit codes: 0 = publishable; 1 = one or more problems (printed one per line
to stdout); 2 = usage / file-not-found / not-UTF-8 (reason printed to stderr).
"""

import argparse
import re
import sys

# Case-insensitive substring blocklist for process/meta narration that must
# never reach a published article. Kept as one tuple so tuning is a single
# diff (NEWS_AGENT_REFACTOR.md risk #1: tune before prod, watch first runs).
META_COMMENTARY = (
    "based on my research",
    "based on the research",
    "i found",
    "here is the article",
    "here's the article",
    "according to my sources",
    "i'll search",
    "i searched",
    "my research",
)

# The "As an AI ..." refusal preamble, as a precise regex rather than a plain
# substring. A bare "as an ai" substring false-blocks legit prose ("as an aide",
# "as an airline") — and a bare `\bas an ai\b` word boundary would instead
# false-block "as an AI researcher / company / model", which is common in tech
# news. So we anchor on the word boundary AND require a model-self-reference
# tail: a comma, a first-person "I", or the canonical "language model" /
# "assistant". That catches "As an AI, I…", "As an AI I cannot…", "As an AI
# language model…" while leaving legit "as an AI <noun>" phrases alone.
AS_AN_AI = re.compile(
    r"\bas an ai\b\s*(?:,|i\b|i['’]|language model|assistant)",
    re.IGNORECASE,
)

WORD_RANGE = (300, 500)
H2_RANGE = (2, 4)

# A "Sources:"/"References:" footer line, optionally bold/heading-wrapped.
SOURCES_FOOTER = re.compile(
    r"^\s*(\*\*|#+\s*)?(sources?|references?)\s*:?\s*(\*\*)?\s*$",
    re.IGNORECASE,
)
# Citation markers: `[<digits>]`. Mirrors crates/managed-agents/src/citations.rs.
CITATION = re.compile(r"\[(\d+)\]")
URL = re.compile(r"https?://")


def strip_citations(text):
    """Remove `[N]` citation markers (NOT `[N](...)` links) so the word count
    reflects prose only. Mirrors the citations.rs grammar: a `]` immediately
    followed by `(` is a markdown link, left in place (its own check flags it).
    Documented in SKILL.md so the model knows markers don't count toward length.
    """
    return re.sub(r"\[\d+\](?!\()", " ", text)


def parse_citations(text, source_count):
    """Return the sorted, deduped list of out-of-range citation indices.

    Mirrors crates/managed-agents/src/citations.rs::parse exactly: scan for
    `[`, consume ASCII digits, require `]`; if that `]` is immediately followed
    by `(` it is a markdown link, not a citation (skip). An index `n` is
    invalid when `n >= source_count`. The golden-fixture agreement test pins
    this against the Rust parser in lockstep.
    """
    invalid = set()
    for m in CITATION.finditer(text):
        end = m.end()
        if end < len(text) and text[end] == "(":
            continue  # `[2024](url)` — a markdown link, not a citation.
        n = int(m.group(1))
        if n >= source_count:
            invalid.add(n)
    return sorted(invalid)


def leading_hashes(line):
    """The run of leading `#` after optional whitespace, with the level — so
    `## ` is H2, `# ` is H1. Returns (level, has_space_after)."""
    stripped = line.lstrip()
    i = 0
    while i < len(stripped) and stripped[i] == "#":
        i += 1
    has_space = i < len(stripped) and stripped[i] == " "
    return i, has_space


def check(text, source_count):
    """Collect every problem (don't stop at the first). Returns a list of
    human/model-readable problem strings; empty == publishable."""
    problems = []
    lines = text.splitlines()

    # 1. No H1 anywhere (`# ` — exactly one hash + space; `## ` is fine).
    for line in lines:
        level, has_space = leading_hashes(line)
        if level == 1 and has_space:
            problems.append("H1 heading found (`# `) — the title renders from "
                            "the Story row; use `## ` sections only")
            break

    # 2. First non-blank line is an H2 section opener.
    first = next((ln for ln in lines if ln.strip()), None)
    if first is not None:
        level, has_space = leading_hashes(first)
        if not (level == 2 and has_space):
            problems.append("first non-blank line must be a `## ` section "
                            "heading (a thematic frame, not the title)")

    # 3. 2-4 H2 sections.
    h2_count = sum(1 for ln in lines if leading_hashes(ln) == (2, True))
    if not (H2_RANGE[0] <= h2_count <= H2_RANGE[1]):
        problems.append(f"{h2_count} H2 sections — need {H2_RANGE[0]}-{H2_RANGE[1]}")

    # 4. Word count 300-500, citation markers excluded.
    words = len(strip_citations(text).split())
    if not (WORD_RANGE[0] <= words <= WORD_RANGE[1]):
        problems.append(f"word count {words} is outside {WORD_RANGE[0]}-{WORD_RANGE[1]} "
                        "(citation markers excluded)")

    # 5. Citation indices in range.
    invalid = parse_citations(text, source_count)
    if invalid:
        rendered = ", ".join(f"[{n}]" for n in invalid)
        problems.append(f"citation(s) out of range (sources: {source_count}, "
                        f"valid 0..{source_count - 1}): {rendered}")

    # 6. No markdown links.
    if "](" in text:
        problems.append("markdown link found (`](`) — the body carries no "
                        "links; source grounding goes through `[N]` markers")

    # 7. No raw URLs.
    if URL.search(text):
        problems.append("raw URL found (`http://`/`https://`) — never put URLs "
                        "in the body; cite via `[N]` markers only")

    # 8. No images.
    if "![" in text:
        problems.append("image markdown found (`![`) — the hero renders from "
                        "the Story row; no images in the body")

    # 9. No Sources/References footer.
    if any(SOURCES_FOOTER.match(ln) for ln in lines):
        problems.append("a `Sources:`/`References:` footer is forbidden — "
                        "citations are `[N]` markers only")

    # 10. No meta-commentary.
    lowered = text.lower()
    for phrase in META_COMMENTARY:
        if phrase in lowered:
            problems.append(f"meta-commentary found ({phrase!r}) — the reader "
                            "sees the article, not your process")
    if AS_AN_AI.search(text):
        problems.append("meta-commentary found ('as an AI ...' self-reference) — "
                        "the reader sees the article, not your process")

    return problems


def main(argv):
    parser = argparse.ArgumentParser(
        description="Check a news story file for publishability.")
    parser.add_argument("--sources", type=int, required=True,
                        help="number of sources (valid citation indices 0..N-1)")
    parser.add_argument("path", help="path to the story markdown file")
    args = parser.parse_args(argv)

    if args.sources < 0:
        print("--sources must be >= 0", file=sys.stderr)
        return 2

    try:
        with open(args.path, "rb") as f:
            raw = f.read()
    except OSError as e:
        print(f"cannot read {args.path}: {e}", file=sys.stderr)
        return 2
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        print(f"{args.path} is not valid UTF-8: {e}", file=sys.stderr)
        return 2

    problems = check(text, args.sources)
    if problems:
        for p in problems:
            print(p)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
