# The Unofficial Guide

Ned, working with the `city_guides` corpus.

---

# Unit 1

## What This Does

<!-- Milestone 5. -->

## Chunking Strategy

**Chunk size:** one chunk per `## ` section of a guide, capped at 900 characters of body text (`CHUNK_SIZE = 900`).
Every chunk starts with a `Guide title > Section heading` label.

**Overlap:** none between sections.
A section longer than 900 characters would be cut at sentence ends with up to 150 characters of whole sentences repeated across the cut (`CHUNK_OVERLAP = 150`), but no section in `city_guides` is that long, so no chunk carries overlap today.

**What about these documents made me pick this.**
The city guides are organised by heading, not by length.
All nine town guides share the same seven sections (Getting there, Getting around, Eat and drink, What to see, Where to stay, When to go, Practical notes), and a question like "how do I get to Kestrelford?" is answered by exactly one of them.
Sections run 175 to 710 characters, so a section already is a right-sized unit.

The starter's `fallback_split` cut every guide into fixed 800-character windows: 51 chunks from 14 documents, 650 characters on average, shortest 24.
Those windows started mid-sentence and straddled two or three sections, so one chunk would hold the end of "Getting around" and the start of "Eat and drink" and match both kinds of question weakly.

The label on top of each chunk matters as much as the split.
"Getting there" in Kestrelford and "Getting there" in Halden Bay read almost the same, and without the label a chunk about bus times does not say which town the buses go to.

**Cleaning (`ingest.py`).**
Every town guide ends with a word-for-word identical "Practical notes" paragraph.
It is a template, not information: it names Brightwater as the nearest full hospital even inside the Brightwater and Marchwood guides, while `guide_accessibility.md` says the nearest full hospital is in Marchwood.
`strip_repeated_sections` drops any section whose body appears in 3 or more documents, which removes those nine copies.
Left in, they would have been nine near-identical chunks competing for every "practical" question.
`clean_text` also strips Markdown bold markers and joins hard-wrapped lines, since some guides wrap at 80 columns and some do not.

**Where I changed my mind.**
My first version kept the paragraph between a guide's title and its first heading as its own "Overview" chunk.
Reading the sample chunks showed that in the cross-cutting guides that paragraph is a line like "An honest assessment rather than a promotional one", which answers nothing on its own.
I now fold that paragraph into the top of the first section.
In the town guides that adds useful context ("a hill town of 12,000, an hour inland from Brightwater") to the Getting there chunk.

**Result:** 75 chunks, 359 characters on average, shortest 188, longest 871.

## Sample Chunks

Printed by `python app.py chunks -n 5`.

**Chunk 1** (source: `guide_accessibility.md#0`, produced by: `chunker.py::split_documents`)

```
Getting around the region with limited mobility > Straightforward

An honest assessment rather than a promotional one. Some of these places are difficult and it is better to know in advance.

Thornby Wells is the easiest town in the region. It is flat, compact, and everything is within three minutes of everything else. Parking is free for two hours anywhere in town and the station is central. The pump room and gardens are level throughout.

Marchwood has a modern tram network with level boarding on all four lines, running every 8 minutes on weekdays. The city museum and covered market are both step-free. The distances between districts are the main consideration.

Brightwater is level along the river and through the centre. The mill museum is step-free. The station is a 15-minute walk from campus on flat ground, or the shuttle meets the four busiest arrivals.
```

**Chunk 2** (source: `guide_corry_vale.md#5`, produced by: `chunker.py::split_documents`)

```
Corry Vale > When to go

May to September. Outside those months the pub in the third village closes, the farm shop reduces its hours, and several footpaths become genuinely boggy rather than merely wet. The road is not gritted above the second village and is impassable in snow.
```

**Chunk 3** (source: `guide_givens_mill.md#3`, produced by: `chunker.py::split_documents`)

```
Givens Mill > What to see

The mill runs tours on the hour from 11 to 3 and the machinery is operating during them, which is loud and much more impressive than a static exhibit. The church has a Saxon doorway. The river walk downstream reaches Brightwater in about three hours.
```

**Chunk 4** (source: `guide_marchwood.md#0`, produced by: `chunker.py::split_documents`)

```
Marchwood > Getting there

Marchwood is the regional hub — 180,000 people, the junction everyone changes trains at, and a city most visitors pass through rather than stop in. That is a mistake, though an understandable one, since almost nothing of interest is near the station.

Every railway line in the region meets here, which is the city's defining feature. Trains to Brightwater run every 40 minutes until 11pm. The airport is 20 minutes out by a dedicated bus that runs every 15 minutes and costs more than the equivalent taxi shared between three people.
```

**Chunk 5** (source: `guide_regional_transport.md#3`, produced by: `chunker.py::split_documents`)

```
Getting around the region > Walking and cycling

The river path from Brightwater runs four miles upstream on a good surface. The old railway trackbed from Kestrelford runs six miles on an easy gradient and is the best walking in the region for the effort involved. The coastal path from Halden Bay is more serious — exposed, and closed in high wind.

Cycling is pleasant on the river path and the trackbed, and unpleasant on Mill Road and the coast road, neither of which has a shoulder.
```

## Sample Answer

<!-- One complete question and answer, pasted as text, with the source line
     visible. Milestone 4. -->

**Question:**

**Answer:**

```
```

**My relevance cutoff:**

<!-- The number you set in config.py, and how you got there.

     You ran five questions your corpus covers and the five in OUT_OF_SCOPE
     that it clearly doesn't, and wrote down the best distance for each. What
     did those two groups look like? Where was the gap? Put the actual numbers
     here — the table below wants all ten rows.

     Milestone 4. -->

| Question | In corpus? | Best distance |
|---|---|---|
|  |  |  |

## How I Used AI

<!-- Two specific moments. For each: what you asked for, what came back, and
     what you changed about it.

     "I asked Claude to write the chunking function from my notes. It ignored
     the overlap, so I added that myself" is the level of detail we're after.
     "I used AI to help me code" is not.

     Milestone 5. -->

**1.**

**2.**

<!-- ── Stretch features ─────────────────────────────────────────────────────
     Doing one? Say so here BEFORE you start. A feature this README never
     claims earns nothing.
     ───────────────────────────────────────────────────────────────────────── -->

---

# Unit 2

<!-- These sections get ADDED to what's already above. Don't delete or rewrite
     unit 1 — the point is that someone can see what you said before you knew
     how it went. -->

## Run Log — Before

<!-- Your five criteria, three runs each. `python run_eval.py --label before`
     runs the questions, puts the OUT_OF_SCOPE ones through the gate, and
     writes it all into results/ for you. Targets come from criteria.md; the
     verdict column is your call.

     Criterion 3 is measured in one deterministic pass rather than three, so
     the same number goes in all three run columns. That's correct, not lazy.

     Milestone 1. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

<!-- Underneath, paste the REAL output for each criterion from one of your
     runs — the actual text your system produced, not a description of it.
     Name the file and function that produced it. -->

## Verdicts

<!-- MET or MISSED for each of the five, against the target you wrote last
     unit — not a new one. Plus a sentence on how you decided. That sentence
     matters most where it was close.

     If your target said 4 of 5 and your runs came out 4, 3, 4, that's a MISS.
     The target has to hold, not show up occasionally.

     Milestone 2. -->

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 |  |  |  |
| 2 |  |  |  |
| 3 |  |  |  |
| 4 |  |  |  |
| 5 |  |  |  |

## Diagnoses

<!-- For each miss: which stage caused it, and how. The stage alone isn't
     enough — you need the mechanism.

     Not a diagnosis: "Question 3 didn't work."
     A diagnosis:     "Question 3 asks about laundry costs. The answer is in
                       one sentence that got split across two chunks, so
                       neither chunk on its own contains it."

     The five stages: loading → chunking → embedding → retrieval → generation.

     Look for a pattern. If three misses all ask about numbers, that's one
     problem, not three.

     Missed nothing? Say so, then say honestly whether your targets were set
     low, and which one you'd tighten and to what.

     Milestone 3. -->

## The Improvement

**What I changed:**

**Why I picked it:**

<!-- Connect it to a specific diagnosis above in one sentence. If you can't,
     you picked a fix because it sounded impressive. -->

### Run Log — After

<!-- Same format, same five criteria, three runs each.
     `python run_eval.py --label after` -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

**Did it help?**

<!-- Say plainly whether it did, and how you know. If it made things worse,
     say that — a change that backfired, honestly reported, earns full credit
     and is more interesting than one that worked. What matters is that you can
     tell.

     Milestone 4. -->

## What's Still Broken

<!-- For each criterion still missed after your fix: what you'd do about it,
     and why you stopped where you did.

     "I ran out of time" is fine if it's true. Pretending nothing is left is
     not.

     Milestone 5. -->

## What I'd Do Differently

<!-- Knowing what you know now — which of your five criteria would you write
     differently, and why?

     Milestone 5. -->
