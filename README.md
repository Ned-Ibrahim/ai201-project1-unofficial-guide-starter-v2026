# The Unofficial Guide

Ned, working with the `city_guides` corpus.

---

# Unit 1

## What This Does

This answers questions about a fictional coastal region from `city_guides`: nine town guides and five cross-cutting guides (eating, walking, regional transport, seasons, accessibility).
It handles practical, factual travel questions such as how often a bus runs, when car parks fill, how late kitchens serve, or which town is manageable with limited mobility.
Each answer is built only from the guide sections retrieved for that question, and it ends with the file it came from.
If nothing in the guides is close enough to the question, it says "I don't have enough information about that." and never calls the model.

Run it with `python app.py ask "your question"` after `python app.py index`.

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

Produced by `python app.py ask "..."`, which runs `store.py::search`, `gate.py::check`, then `generate.py::answer_from_chunks`.

**Question:** Which town in the region is easiest to get around with limited mobility?

**Answer:**

```
  (best distance 0.518, cutoff 0.75)

Thornby Wells is the easiest town in the region to get around with limited mobility because it is flat, compact, and everything is within three minutes of everything else.

Source: guide_accessibility.md

Sources retrieved: guide_accessibility.md, guide_corry_vale.md, guide_halden_bay.md
```

The answer came from the 4th-ranked chunk, not the 1st.
The two Corry Vale chunks above it share the words "getting around" and say nothing about accessibility, and the model ignored them.

**Grounding prompt.**
I kept the starter's `GROUNDING_INSTRUCTION` in `generate.py` and added three rules for this corpus.
Every town guide uses the same section names, so the model has to check which town an excerpt is about before using it, and never move a fact from one town to another.
If two files disagree, it has to name both.
It ends every answer with a `Source: <filename>` line, which makes criterion 2 checkable by reading the last line.

**My relevance cutoff:** 0.75 (`THRESHOLD` in `config.py`), with `TOP_K = 5`.

I ran my five test questions and the five `OUT_OF_SCOPE` questions through `python app.py retrieve` and wrote down the best distance for each.

| Question | In corpus? | Best distance |
|---|---|---|
| How often do buses run from Brightwater to Kestrelford on weekdays? | Yes | 0.234 |
| By what time do the Halden Bay car parks fill up on summer weekends? | Yes | 0.290 |
| How late do kitchens serve in Marchwood on Fridays and Saturdays? | Yes | 0.313 |
| Which town in the region is easiest to get around with limited mobility? | Yes | 0.518 |
| Why do visitors get confused using the buses in the region? | Yes | 0.641 |
| What is the capital of Mongolia? | No | 0.848 |
| How do I change the oil in a diesel engine? | No | 0.905 |
| Who won the 1994 World Cup? | No | 0.997 |
| What is the recommended dosage of ibuprofen for a headache? | No | 0.840 |
| How do I write a for loop in Rust? | No | 0.859 |

The in-corpus group runs 0.234 to 0.641 and the out-of-corpus group runs 0.840 to 0.997, so the gap is 0.641 to 0.840.
I put the cutoff at 0.75, near the middle, about 0.1 clear of each side.

The starter's 0.6 was wrong for this corpus.
It would have refused "Why do visitors get confused using the buses?" (0.641), which `guide_regional_transport.md` answers directly: three bus operators that don't accept each other's tickets.
That question scores worst because it uses none of the guide's own words ("confused" never appears), so it is the one I expect to drift first if I reword anything.

Top-k stays at 5.
For the limited-mobility question, the chunk that names Thornby Wells (`guide_accessibility.md`, "Straightforward") comes back 4th at 0.582, behind two Corry Vale "Getting around" chunks that share words with the question but don't answer it.
At top-k 3 the answer would never reach the model.

## How I Used AI

<!-- Two specific moments. For each: what you asked for, what came back, and
     what you changed about it.

     "I asked Claude to write the chunking function from my notes. It ignored
     the overlap, so I added that myself" is the level of detail we're after.
     "I used AI to help me code" is not.

     Milestone 5. -->

**1.**

I have used AI to help me travers and understand the higher objective. It helped me write the section-based chunker and measure the best distance for all 10 questions in Corb's question. It came back at 0.234 to 0.641 for the on-topic ones and 0.840 to 0.997 for the off-topic ones. It moved the cutoff from the starters, 0.6 to 0.75. It stopped @criteria.md   At this section, because the brief says AI can write criteria, I kept it coded as written.
**2.**

<!-- ── Stretch features ─────────────────────────────────────────────────────
     Doing one? Say so here BEFORE you start. A feature this README never
     claims earns nothing.
     ───────────────────────────────────────────────────────────────────────── -->

---

# Unit 2

## Run Log — Before

`python run_eval.py --label before` asked each of my five questions three times with the response cache off, and put the five `OUT_OF_SCOPE` questions through the gate once.
Raw log: `results/run_2026-09-25_1652_before.md`.
`python tools/check_criteria.py` turned that per-question log into the per-criterion counts below: `results/criteria_2026-09-25_1652_before.txt`.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 2. Every answer names a source | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 4. Chunks: unique header, 150 to 900 chars, end on a sentence | 75 of 75 | 75/75 | 75/75 | 75/75 | MET |
| 5. Q3 says midnight (not 9pm), Q4 says Thornby Wells | 2 of 2 every run | 2/2 | 2/2 | 2/2 | MET |

Criteria 1, 3 and 4 are deterministic (retrieval, a fixed cutoff, and the chunker), so one pass is the measurement and the same number goes in all three columns.
Criteria 2 and 5 depend on generated text and were counted separately for each run.

**How the runs went.**
The first attempt crashed on call 15 with `429 RESOURCE_EXHAUSTED`: `config.REQUESTS_PER_MINUTE` was 30 but the free tier for `gemini-3.5-flash-lite` allows 15, and the retry gave up after 15 seconds while the server asked for 50.
The second attempt returned best distances around 0.9 for every question, because `tools/smoke_test.py` had rebuilt the real index with random stand-in embeddings.
I discarded that run, fixed both harness problems (commits `98fddd7` and `292a559`), re-indexed, and re-ran.
Neither fix touches retrieval, the gate, or the prompt, so the system under test is the one I submitted in unit 1.

### Real output

**Criterion 1**, from `tools/check_criteria.py::criterion_1` (runs `store.py::search`, top-k 5, and `scorer.py::retrieved_contains` on each chunk):

```
1. Retrieved chunk contains the answer: 5/5 (deterministic, same every run)
    rank 1         best 0.234  How often do buses run from Brightwater to Kestrelford on weekdays?
    rank 2         best 0.290  By what time do the Halden Bay car parks fill up on summer weekends?
    rank 2         best 0.313  How late do kitchens serve in Marchwood on Fridays and Saturdays?
    rank 4         best 0.518  Which town in the region is easiest to get around with limited mobility?
    rank 2         best 0.641  Why do visitors get confused using the buses in the region?
```

**Criterion 2**, run 1, from `generate.py::answer_from_chunks` via `run_eval.py::run_once`:

```
Buses run from Brightwater to Kestrelford roughly hourly on weekdays.
Source: guide_kestrelford.md

On summer weekends, parking in the town itself fills by 10am.
Source: guide_halden_bay.md, guide_seasons.md

In Marchwood, kitchens serve until midnight on Fridays and Saturdays.
Source: guide_marchwood.md

Thornby Wells is the easiest town in the region to get around with limited mobility because it is flat, compact, and everything is within three minutes of everything else.
Source: guide_accessibility.md

Visitors get confused because three operators run in the region and they do not accept each other's tickets.
Source: guide_regional_transport.md
```

**Criterion 3**, from `run_eval.py::check_out_of_scope`, cutoff 0.75:

```
| What is the capital of Mongolia? | 0.848 | refused |
| How do I change the oil in a diesel engine? | 0.905 | refused |
| Who won the 1994 World Cup? | 0.997 | refused |
| What is the recommended dosage of ibuprofen for a headache? | 0.840 | refused |
| How do I write a for loop in Rust? | 0.859 | refused |
```

**Criterion 4**, from `tools/check_criteria.py::criterion_4` over `chunker.py::split_documents`:

```
4. 75/75 chunks pass header, length and sentence-end checks
```

**Criterion 5**, all three runs, from `generate.py::answer_from_chunks`:

```
Q3 run 1: In Marchwood, kitchens serve until midnight on Fridays and Saturdays.
Q3 run 2: In Marchwood, kitchens serve until midnight on Fridays and Saturdays.
Q3 run 3: In Marchwood, kitchens serve until midnight on Fridays and Saturdays.
Q4 run 1: Thornby Wells is the easiest town in the region to get around with limited mobility because it is flat, compact, and everything is within three minutes of everything else.
Q4 run 2: Thornby Wells is the easiest town in the region for limited mobility because it is flat, compact, and everything is within three minutes of everything else.
Q4 run 3: Thornby Wells is the easiest town in the region to get around with limited mobility because it is flat, compact, and everything is within three minutes of everything else.
```

## Verdicts

Each verdict is against the target written in `criteria.md` in unit 1, unchanged.

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 | Retrieved chunks contain the answer, 4 of 5 | MET | 5 of 5 questions had a retrieved chunk containing the `expects` phrase. It is closer than 5/5 looks: Q4's answer is the 4th of 5 chunks, so at top-k 3 this would have been 4/5, one question from a miss. |
| 2 | Every answer names a source | MET | 15 of 15 generated answers end with a `Source:` line naming a real file, and each named file contains the fact stated. No refusals happened, so the exclusion in my reason never came into play. |
| 3 | Gate refuses out-of-corpus questions, 4 of 5 | MET | All 5 refused. The closest was ibuprofen at 0.840, 0.09 above the 0.75 cutoff. |
| 4 | 75 chunks, unique header, 150 to 900 characters, sentence end | MET | 75 of 75 pass, shortest 188, longest 871. This one could not have missed: the chunker was built to produce exactly this, and my reason says so. |
| 5 | Q3 says midnight not 9pm, Q4 says Thornby Wells, every run | MET | 6 of 6. No Q3 answer mentions 9pm at all, so there was no borderline case to judge. |

**Arguing the other side.**
The numbers are right. The strongest case against these verdicts is that three of the five targets were close to guaranteed when I wrote them.
Criterion 4 measured the chunker's own design rule.
Criterion 3 had a 0.09 margin I had already measured.
Criterion 1 at top-k 5 counts an answer buried at rank 4 as a success.
The verdicts stand, because the targets are the ones I wrote, but the Diagnoses section treats the near-misses as the real findings.

No criterion was revised: every one could be measured as written, and `tools/check_criteria.py` measures each one the same way every time.

## Diagnoses

**I missed nothing.**
All five criteria were met in all three runs, so there is no failed criterion to diagnose.

**Were my targets set low? Partly, yes.**
Criterion 4 could not fail, since it restates the chunker's design.
Criterion 3's 4 of 5 left room for a miss that my own distances said would not happen.
Criterion 1 is the one I would tighten, because it hides the real weakness in this system.
Written as "the **top-ranked** chunk contains the answer for at least 4 of 5 questions", it would have been **MISSED at 1 of 5** in every run.

**The near-miss: the answer is almost never the closest chunk.**
Printing all five retrieved chunks per question (`*` marks the chunk containing the `expects` phrase):

```
By what time do the Halden Bay car parks fill up on summer weekends?
  1 0.290   Halden Bay > When to go
  2 0.344 * When to visit the region > Summer, June to August
  3 0.385 * Halden Bay > Getting there
How late do kitchens serve in Marchwood on Fridays and Saturdays?
  1 0.313   Eating across the region > Opening hours
  2 0.319 * Marchwood > Eat and drink
Which town in the region is easiest to get around with limited mobility?
  1 0.518   Corry Vale > Getting around
  2 0.530   Corry Vale > Getting there
  3 0.580   Getting around the region with limited mobility > Difficult
  4 0.582 * Getting around the region with limited mobility > Straightforward
Why do visitors get confused using the buses in the region?
  1 0.641   Marchwood > Getting there
  2 0.648 * Getting around the region > Buses
```

Only the Kestrelford bus question has its answer at rank 1.

**Stage: embedding, showing up at retrieval.**
The mechanism is the same in all four cases.
The chunk that wins shares the question's topic words and place name, and the chunk that answers holds the specific fact the question turns on.

- Q2: "Halden Bay > When to go" wins on Halden Bay + summer + parking ("the parking problem becomes the defining feature").
  The time, "fill by 10am", is in "Getting there", ranked 3rd.
- Q3: "Eating across the region > Opening hours" wins on kitchens + serving + Marchwood, and that chunk says kitchens stop at 9pm.
  "Until midnight on Fridays and Saturdays" is in "Marchwood > Eat and drink", 0.006 further away.
- Q4: "Corry Vale > Getting around" wins on the literal words "getting around", which my own `Guide > Section` header puts at the top of every Getting around chunk.
  The answering chunk's header ends in "Straightforward", a word the question never uses.
  This one is partly a chunking effect: the header I added to disambiguate towns also makes section names like "Getting around" count for more.
- Q5: "Marchwood > Getting there" wins on "bus" (the airport bus).
  The answer, three operators not accepting each other's tickets, shares no words with "confused".

all-MiniLM-L6-v2 turns each 200 to 800 character chunk into one 384-number vector, and that vector is dominated by what the chunk is about.
A single decisive detail (a time, a town name in a list, "operators") barely moves it.
So the model ranks by topic and gets the topic right, but the ordering within a topic is close to a coin flip: 0.006 and 0.007 separate rank 1 from the answer in Q3 and Q5.

**Why it has not broken anything yet.**
Top-k 5 is wide enough to catch rank 4, and the grounding prompt makes the model read past the wrong-town and wrong-time chunks.
Both are safety nets for a retrieval ordering problem, and the model is doing work retrieval should have done.
One more Corry Vale-style distractor for Q4 and the answer falls out of the top 5.

## The Improvement

**What I changed:** hybrid search.
`store.py::search` now ranks every chunk twice, once by meaning (cosine distance from all-MiniLM-L6-v2) and once by keywords (BM25 via `rank-bm25`), and merges the two lists with reciprocal rank fusion: `score = 1/(60 + meaning rank) + 1/(60 + keyword rank)`.
The top 5 by that score go to the gate and the model.
Every result keeps its real cosine distance, so the gate still compares a cosine distance against the same 0.75 cutoff.
`config.HYBRID` switches it on; `False` is exactly the unit 1 system.

**Why I picked it:** the diagnosis found the answer chunk ranked first for only 1 of 5 questions because the embedding ranks by topic, and BM25 ranks by the exact words ("Fridays", "limited mobility", "buses") the embedding glides past.

**Other commits in this unit, and why they are not a second change.**
Before the baseline could run at all I fixed three things in the test harness: the rate limiter (`config.REQUESTS_PER_MINUTE`, `generate.py::_server_retry_delay`), `tools/smoke_test.py` overwriting the real index, and the smoke test's ordering check once hybrid existed.
I also added `tools/check_criteria.py` to count each criterion.
None of these changes what the system retrieves, gates, or generates for a question.

### Run Log — After

Raw log: `results/run_2026-09-25_1657_after.md`.
Per-criterion counts: `results/criteria_2026-09-25_1657_after.txt`.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 2. Every answer names a source | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 4. Chunks: unique header, 150 to 900 chars, end on a sentence | 75 of 75 | 75/75 | 75/75 | 75/75 | MET |
| 5. Q3 says midnight (not 9pm), Q4 says Thornby Wells | 2 of 2 every run | 2/2 | 2/2 | 2/2 | MET |

**Before and after on the thing the change was aimed at**, from `tools/check_criteria.py::criterion_1` (rank of the first retrieved chunk containing the `expects` phrase):

| Question | Rank before | Rank after | Best distance before | Best distance after |
|---|---|---|---|---|
| Q1 Kestrelford buses | 1 | 1 | 0.234 | 0.234 |
| Q2 Halden Bay car parks | 2 | **1** | 0.290 | 0.344 |
| Q3 Marchwood kitchens | 2 | 2 | 0.313 | 0.313 |
| Q4 limited mobility | 4 | **1** | 0.518 | 0.580 |
| Q5 bus confusion | 2 | **1** | 0.641 | 0.641 |
| **Answer at rank 1** | **1 of 5** | **4 of 5** | | |

Out-of-scope best distances after: 0.848, 0.905, 1.008, 0.840, 0.859 (before: 0.848, 0.905, 0.997, 0.840, 0.859).

Real output, criterion 5 after, all three runs:

```
Q3 run 1: In Marchwood, kitchens serve until midnight on Fridays and Saturdays.
Q3 run 2: In Marchwood, kitchens serve until midnight on Fridays and Saturdays.
Q3 run 3: In Marchwood, kitchens serve until midnight on Fridays and Saturdays.
Q4 run 1: Thornby Wells is the easiest town in the region to get around with limited mobility because it is flat, compact, and everything is within three minutes of everything else.
Q4 run 2: Thornby Wells is the easiest town in the region to get around with limited mobility because it is flat, compact, and everything is within a three-minute walk.
Q4 run 3: Thornby Wells is the easiest town in the region for getting around with limited mobility because it is flat, compact, and everything is within a three-minute walk.
```

**Did it help?**
Yes for retrieval ordering, and invisibly to my five criteria.
The answer chunk now ranks first for 4 of 5 questions instead of 1 of 5, and the Q4 answer moved from 4th, one place from falling out of the top 5, to 1st.
The five criteria read MET before and MET after, so by my own run log nothing changed.
That says more about my criteria than about the fix. None of them measured rank, so they could not see the problem or the repair.

It also had two costs.
For Q2 and Q4 the chunk nearest in meaning is no longer in the top 5, so the gate now sees a best distance of 0.344 instead of 0.290 and 0.580 instead of 0.518.
Both are still far under 0.75, but hybrid search pushes in-corpus questions toward the cutoff, never away from it.
And Q2's answer now cites three files instead of two, because the regional transport guide's "Both Halden Bay lots fill by 10am on summer weekends" made it into the top 5; that citation is correct, just longer.

## What's Still Broken

**No criterion is missed**, before or after, so there is no failing criterion to carry forward.
What is still wrong:

- **Q3 still ranks the wrong chunk first.**
  The meaning ranking puts "Eating across the region > Opening hours" 1st and "Marchwood > Eat and drink" 2nd, and BM25 puts them the other way round.
  Reciprocal rank fusion then gives both exactly 1/61 + 1/62, and the tie falls back to the meaning order.
  The model still answers correctly because the grounding prompt tells it to check which town an excerpt is about.
  To fix it I would weight BM25 higher for questions that name a town, or boost a chunk whose header names the town in the question.
  I stopped here because either is a second change, and this unit allows one.
- **The gate margin got smaller.**
  Q4's best distance moved from 0.518 to 0.580.
  Hybrid search can only ever raise the best distance the gate sees, since it may drop the nearest chunk from the top 5.
  I would gate on the nearest chunk overall rather than the nearest one returned, which keeps the unit 1 cutoff meaning exactly what it did.
- **Paraphrase drift.**
  In two of three Q4 runs after the change the model wrote "within a three-minute walk"; the guide says "within three minutes of everything else".
  It is a small change in meaning that no criterion catches.
  A criterion checking that stated numbers appear word for word in the cited file would.

## What I'd Do Differently

I would rewrite criterion 1 to measure rank instead of presence: "for at least 4 of 5 questions, the top-ranked chunk contains the answer."
As written it passed 5 of 5 while the answer sat first for only 1 question, and it could not tell before from after.

I would drop criterion 4 or make it about retrieval quality instead of chunk shape.
It restated my chunker's design, so it could not fail, and it said nothing about whether the chunks were the right size for answering.

I would keep criteria 2, 3 and 5.
Criterion 5 was the one that tested something real, whether the model used the right chunk when a wrong one ranked above it, and I would write more criteria like it.

