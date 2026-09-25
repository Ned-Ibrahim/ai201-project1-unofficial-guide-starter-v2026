#!/usr/bin/env python3
"""
Turn a run log into one row per criterion, the way the README's run log wants.

    python tools/check_criteria.py results/run_..._before.md

`run_eval.py` writes one row per QUESTION. This reads that file (for the
criteria that depend on generated answers) and re-runs the deterministic parts
itself (retrieval and chunking), then prints a count per criterion per run.

It measures; it changes nothing. Targets come from criteria.md:

  1. For at least 4 of 5 test questions, the retrieved chunks include one that
     contains the answer. "Contains the answer" = contains the question's
     `expects` phrase (scorer.retrieved_contains). Retrieval is deterministic,
     so one pass is the measurement for all three runs.
  2. Every generated answer names a source file (scorer.names_source).
     Refusals are excluded, per the reason under criterion 2.
  3. Read straight from the run log's out-of-scope table.
  4. All chunks begin with a unique "Guide > Section" header, are 150 to 900
     characters, and end at a sentence boundary.
  5. Q3 contains "midnight" and does not give 9pm as Marchwood's Friday and
     Saturday closing time; Q4 contains "Thornby Wells". Per run.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import gate  # noqa: E402
import questions as qs  # noqa: E402
from chunker import split_documents  # noqa: E402
from ingest import load_documents  # noqa: E402
from scorer import contains, names_source  # noqa: E402
from store import search  # noqa: E402

ENTRY = re.compile(r"^### ([^\n]+) — run (\d+)\n(.*?)```\n(.*?)\n```", re.M | re.S)
GATE_ROW = re.compile(r"^\| (.+?) \| ([\d.]+) \| (refused|\*\*let through\*\*) \|$", re.M)


def answers_by_run(log: str) -> dict[int, dict[str, str]]:
    runs: dict[int, dict[str, str]] = {}
    for question, run, _, answer in ENTRY.findall(log):
        runs.setdefault(int(run), {})[question] = answer.strip()
    return runs


def criterion_1() -> tuple[int, list[str]]:
    lines, hits = [], 0
    for item in qs.answered():
        results = search(item["question"])
        ranks = [i for i, r in enumerate(results, 1) if contains(r.text, item["expects"])]
        hits += bool(ranks)
        where = f"rank {ranks[0]}" if ranks else "not retrieved"
        lines.append(f"    {where:<14} best {min(r.distance for r in results):.3f}  {item['question']}")
    return hits, lines


def criterion_2(answers: dict[str, str]) -> tuple[int, int]:
    generated = [a for a in answers.values() if a != gate.REFUSAL]
    return sum(names_source(a) for a in generated), len(generated)


def criterion_3(log: str) -> tuple[int, int]:
    rows = GATE_ROW.findall(log)
    return sum(verdict == "refused" for _, _, verdict in rows), len(rows)


def criterion_4() -> tuple[int, int, list[str]]:
    chunks = split_documents(load_documents())
    headers = [c.text.split("\n", 1)[0] for c in chunks]
    problems = []
    for chunk, header in zip(chunks, headers):
        if " > " not in header:
            problems.append(f"{chunk.label}: no 'Guide > Section' header")
        if headers.count(header) > 1:
            problems.append(f"{chunk.label}: header shared: {header}")
        if not 150 <= len(chunk.text) <= 900:
            problems.append(f"{chunk.label}: {len(chunk.text)} characters")
        if not chunk.text.rstrip().endswith((".", "!", "?")):
            problems.append(f"{chunk.label}: ends mid-sentence")
    bad = {p.split(":")[0] for p in problems}
    return len(chunks) - len(bad), len(chunks), problems


def _question(number: int) -> str:
    return qs.answered()[number - 1]["question"]


def criterion_5(answers: dict[str, str]) -> tuple[int, list[str]]:
    q3, q4 = answers.get(_question(3), ""), answers.get(_question(4), "")
    marchwood_9pm = re.search(r"\b9\s*(pm|p\.m\.|:00)", q3, re.I) is not None
    checks = {
        "Q3 midnight": contains(q3, "midnight") and not marchwood_9pm,
        "Q4 Thornby Wells": contains(q4, "Thornby Wells"),
    }
    return sum(checks.values()), [k for k, ok in checks.items() if not ok]


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: python tools/check_criteria.py results/run_....md")
    log = Path(sys.argv[1]).read_text(encoding="utf-8")
    runs = answers_by_run(log)

    c1, c1_lines = criterion_1()
    print(f"1. Retrieved chunk contains the answer: {c1}/5 (deterministic, same every run)")
    print("\n".join(c1_lines))

    for run in sorted(runs):
        named, total = criterion_2(runs[run])
        print(f"2. Run {run}: {named}/{total} generated answers name a source")

    refused, total = criterion_3(log)
    print(f"3. Gate refused {refused}/{total} out-of-scope questions (deterministic)")

    ok, total, problems = criterion_4()
    print(f"4. {ok}/{total} chunks pass header, length and sentence-end checks")
    for problem in problems:
        print(f"    {problem}")

    for run in sorted(runs):
        passed, failed = criterion_5(runs[run])
        extra = f"  failed: {', '.join(failed)}" if failed else ""
        print(f"5. Run {run}: {passed}/2{extra}")


if __name__ == "__main__":
    main()
