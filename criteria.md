# Acceptance criteria — The Unofficial Guide

Five criteria that say what "working" means for this system, written in unit 1
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"Retrieval works"* is an opinion. *"For at
least 4 of my 5 test questions, the top results include a chunk containing the
answer"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter or looser one. A reason that says something about your corpus or your
pipeline earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## 1. Retrieved chunks contain the answer

For at least 4 of my 5 test questions, the retrieved chunks include one that
contains the answer.

**Why this target:**

Retrieval sets the ceiling for everything after it, because the model can't answer from a chunk it never sees. My two known weak spots are Q4 (the answer is at rank 4 of 5, behind two Corry Vale chunks that share the words "getting around") and Q3 (the answer is at rank 2, behind a chunk saying kitchens outside Marchwood stop at 9pm). Both are still inside top-k = 5, so 4 of 5 is realistic. It leaves room for one miss if wording changes, and it is not so low that a real retrieval failure would pass unnoticed.

---

## 2. Every answer names a source

Every answer the system produces names at least one source document.

**Why this target:**

A RAG answer is only useful if a reader can check it, and a source filename is how they do that. "Every answer" means every answer the model generates. Gate refusals are excluded because they never reach the model. 100% is fair because the prompt requires an ending line of "Source: <filename>", and a pattern match can check it. Since generation varies between runs, three runs per question test whether the prompt produces the citation reliably. A citation only shows that a source is named, not that it's the right one, which is why criterion 5 checks correctness.

---

## 3. The relevance gate stops out-of-corpus questions

When I ask a question my documents clearly don't cover, the relevance gate
stops it and the system returns "I don't have enough information about that" —
in at least 4 of 5 tries.

**Why this target:**

My measurements make this a fair test. The five off-topic questions had best distances of 0.840 to 0.997, all above the 0.75 cutoff, and my worst in-corpus question was 0.641. That leaves a margin of roughly 0.09 to 0.11 on each side. Five questions is a small sample, and an off-topic question that shares vocabulary with the guides could land under 0.75. Requiring 4 of 5 tolerates one such near miss without passing a leaky gate. The gate should also never refuse my in-corpus questions, and the data shows it doesn't. The starter's 0.6 cutoff would have wrongly refused Q5.

---

## 4. Something about your chunks

All 75 chunks begin with a "Guide > Section" header, no two chunks share the same header, and every chunk is between 150 and 900 characters and ends at a sentence boundary. A script checks this.

**Why this target:**

This is what my chunker was designed to guarantee, and the starter's fixed 800-character chunker failed it (51 chunks, one only 24 characters long, headings cut through). The unique-header check matters most. My nine town guides share the same six section names, so the town name in the header is what stops "Eat and drink" in Marchwood from being mistaken for the same section in Halden Bay. The size bounds catch fragments that embed poorly and oversized chunks that dilute the embedding. My current range (188 to 871 characters) already passes, so the check also works as a regression test if I change the chunker later.

---

## 5. Your choice

Q3's answer contains "midnight" and Q4's answer contains "Thornby Wells" in 3 of 3 runs each (6 of 6 total). Q3's answer must also not give 9pm as Marchwood's Friday and Saturday closing time.

**Why this target:**

This tests the risk I found in my own measurements. Retrieval can succeed while generation still fails: Q3's top chunk gives the wrong time and the right one sits second, and Q4's answer is at rank 4 behind two off-target chunks. Criterion 1 only checks that the right chunk was retrieved, not that the model used it. The target is hard but achievable, since the prompt tells the model to check that each excerpt is about the right town. If it misses, the diagnosis is useful: the model may be trusting rank order, the prompt's town check may be too weak, or the chunk headers may need to be more prominent. Requiring 3 of 3 runs checks consistency, not one lucky success.

---

