#!/usr/bin/env python3
"""Fixtures test for check_story.py — the news agent's publish gate.

This script IS the contract the checker's docstring promises. In file-driven
publish mode, `submit_story` runs check_story.py as the SOLE gate (the in-Rust
H1/citation guards are skipped), so the production-incident invariants —
no-H1-in-body and citation-indices-in-range — are protected ONLY by this
script. Run after any edit:

    python3 test_check_story.py     # stdlib unittest, no pip deps

A change that drops a check fails here loudly.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_story  # noqa: E402


def good_body():
    """A clean ~330-word, 2-H2-section article citing [0] and [1]."""
    s1 = (
        "The company reported record quarterly revenue driven by surging demand "
        "for its networking hardware from large cloud customers.[0] "
    )
    s2 = (
        "Analysts raised their price targets after the results, citing a "
        "multi-year order backlog and steadily improving margins.[1] "
    )
    return "## A record quarter\n\n" + (s1 * 9) + "\n\n## What analysts expect\n\n" + (s2 * 9)


class CheckStoryFixtures(unittest.TestCase):
    def test_clean_story_passes(self):
        # Sanity-check the fixture is in range, then assert it's publishable.
        self.assertEqual(check_story.check(good_body(), source_count=2), [])

    def test_h1_in_body_is_rejected(self):
        # Production incident: an H1 duplicates the Story-row title on the page.
        body = "# Cisco hits a record\n\n" + good_body()
        problems = check_story.check(body, source_count=2)
        self.assertTrue(any("H1" in p for p in problems), problems)

    def test_out_of_range_citation_is_rejected(self):
        # Production incident: [40] against a 4-source array hid the sources block.
        body = good_body().replace("[1]", "[40]", 1)
        problems = check_story.check(body, source_count=2)
        self.assertTrue(
            any("out of range" in p and "[40]" in p for p in problems), problems
        )

    def test_meta_commentary_is_rejected(self):
        body = good_body() + "\n\nBased on my research, this is the story.[0]"
        problems = check_story.check(body, source_count=2)
        self.assertTrue(any("meta-commentary" in p for p in problems), problems)

    def test_word_count_bounds(self):
        # Citation markers are stripped before counting; too-short fails.
        short = "## Frame\n\nToo short.[0]\n\n## Second\n\nStill short.[1]"
        problems = check_story.check(short, source_count=2)
        self.assertTrue(any("word count" in p for p in problems), problems)

    def test_markdown_link_and_raw_url_rejected(self):
        body = good_body() + "\n\nSee [the report](https://example.com) for more."
        problems = check_story.check(body, source_count=2)
        self.assertTrue(any("markdown link" in p for p in problems), problems)
        self.assertTrue(any("raw URL" in p for p in problems), problems)


if __name__ == "__main__":
    unittest.main()
