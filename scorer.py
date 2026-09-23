"""
Decides whether one answer was right. `run_eval.py` finds this file and calls
`judge` for every question on every run.

"Right" here means two things, both checkable by reading the answer text:

  1. It contains the `expects` phrase from questions.py, which was written in
     unit 1 before any answers existed.
  2. It names at least one source file from the corpus.

A refusal is never right: every question in QUESTIONS is one the corpus
answers, so the gate or the model declining is a miss.

`retrieved_contains` is the retrieval-side check for criterion 1. It looks at
the chunks, not the answer, so it can tell a retrieval miss apart from a
generation miss on the same question.
"""

import re

from gate import REFUSAL

SOURCE_FILE = re.compile(r"\b[\w-]+\.(?:md|txt)\b")


def _normalise(text: str) -> str:
    """Lowercase, one space everywhere, and "10 am" / "10:00am" read as "10am"."""
    text = text.lower().replace("’", "'")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"(\d)(?::00)?\s*(am|pm)\b", r"\1\2", text)
    return text


def contains(text: str, expects: str) -> bool:
    return _normalise(expects) in _normalise(text)


def names_source(answer: str) -> bool:
    return SOURCE_FILE.search(answer) is not None


def retrieved_contains(expects: str, results) -> bool:
    """Criterion 1: does any retrieved chunk contain the expected phrase?"""
    return any(contains(r.text, expects) for r in results)


def judge(question: str, expects: str, answer: str, results) -> bool:
    if answer.strip() == REFUSAL:
        return False
    return contains(answer, expects) and names_source(answer)
