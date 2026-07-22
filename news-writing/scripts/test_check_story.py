#!/usr/bin/env python3
"""Fixtures test for check_story.py — the news agent's publish gate.

This script IS the contract the checker's docstring promises. In file-driven
publish mode, `submit_story` re-runs check_story.py as the deterministic VM
gate, while the service independently enforces source/citation-count guards so
stale VM checker copies cannot publish under-sourced stories. Run after any
edit:

    python3 test_check_story.py     # stdlib unittest, no pip deps

A change that drops a check fails here loudly.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_story  # noqa: E402


def good_body():
    """A clean ~330-word, 2-H2-section article citing [1] through [5]."""
    claims = [
        "The company reported record quarterly revenue driven by surging demand "
        "for its networking hardware from large cloud customers.[1] ",
        "Executives said AI infrastructure orders remained a major growth driver "
        "as cloud buyers expanded capacity.[2] ",
        "Analysts raised their price targets after the results, citing a "
        "multi-year order backlog and steadily improving margins.[3] ",
        "The company also pointed to stronger enterprise demand outside the "
        "largest hyperscale accounts.[4] ",
        "Market watchers compared the rally with earlier dot-com milestones, "
        "while warning that infrastructure cycles can turn quickly.[5] ",
    ]
    s1 = "".join(claims)
    s2 = "".join(reversed(claims))
    return "## A record quarter\n\n" + (s1 * 3) + "\n\n## What analysts expect\n\n" + (s2 * 2)


class CheckStoryFixtures(unittest.TestCase):
    def test_clean_story_passes(self):
        # Sanity-check the fixture is in range, then assert it's publishable.
        self.assertEqual(check_story.check(good_body(), source_count=5), [])

    def test_h1_in_body_is_rejected(self):
        # Production incident: an H1 duplicates the Story-row title on the page.
        body = "# Cisco hits a record\n\n" + good_body()
        problems = check_story.check(body, source_count=5)
        self.assertTrue(any("H1" in p for p in problems), problems)

    def test_out_of_range_citation_is_rejected(self):
        # Production incident: [41] against a 5-source array hid the sources block.
        body = good_body().replace("[2]", "[41]", 1)
        problems = check_story.check(body, source_count=5)
        self.assertTrue(
            any("out of range" in p and "[41]" in p for p in problems), problems
        )

    def test_zero_citation_is_rejected(self):
        body = good_body().replace("[1]", "[0]", 1)
        problems = check_story.check(body, source_count=5)
        self.assertTrue(
            any("out of range" in p and "[0]" in p for p in problems), problems
        )

    def test_meta_commentary_is_rejected(self):
        body = good_body() + "\n\nBased on my research, this is the story.[1]"
        problems = check_story.check(body, source_count=5)
        self.assertTrue(any("meta-commentary" in p for p in problems), problems)

    def test_word_count_bounds(self):
        # Citation markers are stripped before counting; too-short fails.
        short = "## Frame\n\nToo short.[1][2][3]\n\n## Second\n\nStill short.[4][5]"
        problems = check_story.check(short, source_count=5)
        self.assertTrue(any("word count" in p for p in problems), problems)

    def test_markdown_link_and_raw_url_rejected(self):
        body = good_body() + "\n\nSee [the report](https://example.com) for more."
        problems = check_story.check(body, source_count=5)
        self.assertTrue(any("markdown link" in p for p in problems), problems)
        self.assertTrue(any("raw URL" in p for p in problems), problems)

    def test_source_count_minimum_is_rejected(self):
        problems = check_story.check(good_body(), source_count=4)
        self.assertTrue(any("4 sources" in p and "at least 5" in p for p in problems), problems)

    def test_distinct_cited_source_minimum_is_rejected(self):
        body = good_body().replace("[2]", "[1]").replace("[3]", "[1]").replace("[4]", "[1]").replace("[5]", "[1]")
        problems = check_story.check(body, source_count=5)
        self.assertTrue(any("distinct cited source" in p and "need at least 5" in p for p in problems), problems)


if __name__ == "__main__":
    unittest.main()
