---
name: news-writing
description: House style, output shape, and citation rules for the news agent's published article, plus the checker you run to verify the draft before publishing. Read this before writing story.md.
---

# News writing

This is the style rulebook and verification guide for the article you write to
`story.md`. Read it before you start writing, and verify your draft against the
checker (see "How to verify your draft") before calling `submit_story`.

## Output shape

300–500 words across 2–4 H2 sections (most posts settle at 2 or 3 sections).
Inline citation markers wherever you cite a number, quote, or specific claim.
Every story must cite at least 5 distinct source URLs.

Hard requirements:
- **NO H1 in the body.** The article title lives on the Story row and is
  rendered by the frontend separately. Putting an H1 in the body duplicates it
  on the published page. Do not include the article title anywhere in the body
  — neither as `# Title` nor as the opening sentence.
- **NO leading image markdown.** The hero image is rendered by the frontend
  from the Story row's `mainImageUrl` field. Do not put `![alt](url)` at the
  top of the body.
- **First line is an H2 section heading**, framed thematically
  (e.g. `## A swearing-in stripped of its script`) — NOT a repeat or paraphrase
  of the article title.
- **The opening paragraph lives under the first H2.** Specific numbers, dates,
  named players. 2–4 sentences. It can reference context implied by the title
  ("The remarks come as…") because the title renders above it on the page.
- **2–4 H2 sections total**, each with one subhead and 1–2 paragraphs of body.
  Subheads are descriptive statements, not questions.
- **Citation markers** as `[N]` brackets — see Citation rules below.
- **At least 5 distinct cited source URLs** in the finished article.
- **No image credit line** in the body. The body ends with the last paragraph
  of the last H2 section. Hero metadata (image, credit) lives on the Story row
  and renders separately.
- **Total length 300–500 words** for the article body. Citation markers (`[N]`)
  do NOT count toward the word total — the checker strips them before counting,
  so write 300–500 words of prose.

Forbidden:
- An H1 (`# Heading`) anywhere in the body — see above.
- Meta-commentary ("based on the research", "I found", "my sources").
- Hedging filler ("It is important to note that…", "Notably,…").
- A standalone "Sources:" or "References:" footer.
- Bullet lists (unless the topic literally demands them — e.g. a numbered
  ranking).
- The article title appearing in any heading or sentence in the body.

## Citation rules

You cite sources using `[N]` markers where `N` is the 0-indexed position of the
source URL in the conversation. Count URLs in the order they first appear in
your tool results — including every URL inside every per-query section of a
batched `news_search` / `web_search` (sections are headed
`## News search: "<query>"`), and every URL returned by `web_fetch`. Indices
accrue across the WHOLE conversation in first-seen order, not per-tool-call. If
a URL appears twice, reuse the index from its first appearance. `find_topic` /
`find_hero_image` run their own internal searches whose URLs do NOT enter your
citation list — only count URLs from `news_search`, `web_search`, and
`web_fetch` results you receive.
The finished article must cite at least 5 distinct valid source indices.

- 0-indexed brackets at the end of the sentence the source supports:
  "Cisco shares closed at $77.38[0][2]."
- Each index in its own brackets: `[0][1]`, never `[0, 1]`.
- Max 2 citations per claim. Never repeat the same index in one group —
  `[0][3][0]` is forbidden.
- Never explain citations inline ("[0][3] refer to the Reuters pieces"). The
  bracket IS the citation; do not narrate it.
- Cite only claims sourced from a tool result. Never cite filler or general
  knowledge.
- No space between the last word and the citation.
- **Never include raw URLs in the article body.** All source grounding goes
  through `[N]` markers only — no `(https://...)`, no `[text](url)` markdown
  links, nothing. The frontend will map `[N]` back to the URL from the tool log.
- No "Sources" or "References" footer at the end.

## Worked example

This is the target shape. Match the structure, density, and citation form. The
numeric indices below assume the agent issued one batched `news_search` with
several queries (yielding URLs at positions 0–4 in first-seen order) and one
batched `web_fetch` on those same URLs (which dedup to their original
positions 0–4). Indices are deterministic from tool-result order; you don't
pick them.

The article title for this story — *"Cisco stock surpasses dot-com peak, raising
AI bubble fears"* — lives on the Story row and renders above the body on the
published page. The body below does NOT repeat it.

```markdown
## A symbolic milestone, 25 years late

Cisco Systems shares closed at $77.38 on November 13, 2025, surpassing its
all-time closing high of $77.31 set during the dot-com bubble in March 2000.[0]
The 4.6% surge followed better-than-expected quarterly earnings driven by
surging demand for AI networking equipment.[1] The milestone is stoking fears
that the current AI boom may be approaching a dangerous inflection point, with
analysts warning that network equipment investments typically occur in the
final stages of infrastructure spending cycles.[0]

## Strong earnings on AI infrastructure orders

The networking giant reported first-quarter revenue of $14.9 billion, up 8%
year-over-year, and non-GAAP earnings per share of $1.00, exceeding guidance.[1]
Most notably, AI infrastructure orders from hyperscaler customers totaled $1.3
billion in the quarter, reflecting what the company called "a significant
acceleration in growth".[1] Cisco expects $3 billion in AI infrastructure
revenue from hyperscalers in fiscal 2026, up from $1 billion in fiscal 2025.[1]

## Echoes of 2000 raise bubble warnings

The symbolic milestone has intensified scrutiny of AI valuations. During the
dot-com era, Cisco briefly became the world's most valuable company before its
stock plummeted 88% when the bubble burst.[2] Lisa Shalett, chief investment
officer at Morgan Stanley Wealth Management, has warned the market could face a
"Cisco moment" within 24 months — a scenario where AI stocks collapse similar
to the dot-com crash.[3] Goldman Sachs strategists have separately cautioned
that the biggest platform companies are absorbing a growing share of index
returns, leaving the market more exposed if AI capital spending slows.[4]

## Late-cycle signal or sustainable growth

Network equipment investments typically occur in the final stages of IT
infrastructure buildouts.[0] Hyperscalers are projected to spend approximately
$405 billion on AI infrastructure in 2025, with estimates reaching $602 billion
in 2026.[0] JPMorgan, Bank of America, and Wells Fargo have raised their price
targets following the earnings report — but the central question remains whether
Cisco's return to dot-com heights signals a peak or the start of a sustained
cycle.[1][4]
```

That's the shape. NO H1, NO repeat of the article title (it renders separately
from the Story row), first line is an H2 section heading framed thematically,
opening paragraph lives under that first H2. 2–4 H2 sections each with 1–2
paragraphs, `[N]` markers where claims need sourcing, ~400 words. No filler, no
process-talk, no `Sources:` footer, no raw URLs in the body, no `*Image: ...*`
credit line.

## How to verify your draft

A deterministic checker is baked into this VM alongside this skill at
`/mnt/skills/news-writing/scripts/check_story.py`, so you verify the article
yourself and fix every problem before you publish.

1. Write (and edit) the article at `/workspace/story.md` using `apply_patch`.
   Make surgical edits when fixing problems — never re-emit the whole article to
   chat.
2. Run the checker via the `shell` tool, passing the number of sources you will
   pass to `submit_story` as `N`. `N` must be at least 5, and the body must cite
   at least 5 distinct valid source indices:

   ```
   python3 /mnt/skills/news-writing/scripts/check_story.py --sources N /workspace/story.md
   ```

3. **Exit 0 with no output ⇒ the draft is publishable.** Any other exit prints
   one problem per line — fix exactly those (surgical `apply_patch` edits), then
   re-run. Repeat until it exits 0.
4. The word count excludes `[N]` citation markers — the checker strips them
   before counting, so aim for 300–500 words of prose.
5. Only publish once the checker exits 0. Then call `submit_story` once with the
   metadata — it reads the article body straight from `/workspace/story.md` and
   re-runs this same checker as the publish gate, so you never paste the article
   into chat or pass the body as an argument.
