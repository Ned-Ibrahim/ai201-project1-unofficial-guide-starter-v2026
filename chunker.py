"""
Stage 2 of the pipeline: splitting documents into chunks.

⚠️ THIS IS THE FILE YOU CHANGE IN MILESTONE 3.

`split_documents` below is deliberately plain. It cuts every document into
fixed-size pieces with a fixed overlap and pays no attention to where sentences
or paragraphs end. It works, and it is not good.

On a corpus of short posts it may not cut anything at all: `campus_life` comes
out as 88 documents and 88 chunks, because almost nothing in it reaches 800
characters. That is the baseline, not a bug — Milestone 3 is where you decide
whether one post should stay one chunk.

Your job in Milestone 3 is to replace the *body* of `split_documents` with a
strategy that fits the documents you actually read in Milestone 1. Keep the
name and the shape of what it returns — the rest of the pipeline calls it, and
your README has to name the function that produced your chunks.

If you get stuck for 30 minutes, `fallback_split` is the original. Switch back
to it, write down what you saw, and move on. That's a real observation about
your pipeline, not giving up.
"""

import re
from dataclasses import dataclass

import config
from ingest import Document


@dataclass
class Chunk:
    """One piece of one document."""

    text: str
    source: str        # which file it came from
    index: int         # which chunk within that file, starting at 0
    produced_by: str   # the function that made it — cite this in your README

    @property
    def label(self) -> str:
        return f"{self.source}#{self.index}"


def fallback_split(
    documents: list[Document],
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[Chunk]:
    """
    The starter's original chunker. Fixed-size character windows with overlap.

    Keep this function. Milestone 3's stop rule points back at it, and having
    something to compare your own strategy against is useful in unit 2.
    """
    chunk_size = chunk_size or config.CHUNK_SIZE
    overlap = overlap or config.CHUNK_OVERLAP

    if overlap >= chunk_size:
        raise ValueError("overlap has to be smaller than chunk_size")

    chunks: list[Chunk] = []
    for doc in documents:
        start = 0
        index = 0
        while start < len(doc.text):
            piece = doc.text[start : start + chunk_size].strip()
            if piece:
                chunks.append(
                    Chunk(
                        text=piece,
                        source=doc.source,
                        index=index,
                        produced_by="chunker.py::fallback_split",
                    )
                )
                index += 1
            start += chunk_size - overlap

    return chunks


_HEADING = re.compile(r"(?m)^(#{1,2}) +(.+?)\s*$")


def _sections(text: str) -> tuple[str, list[tuple[str, str]]]:
    """
    Break one guide into (heading, body) pairs.

    Returns the document title (the `# ` line) and every section under it.
    Text between the title and the first `## ` is folded into the top of the
    first section rather than kept on its own. In the town guides that
    paragraph says what the town is ("a hill town of 12,000, an hour inland
    from Brightwater"), which is context the first section benefits from. In
    the cross-cutting guides it is a line like "An honest assessment rather
    than a promotional one", which answers nothing by itself.
    """
    title = ""
    sections: list[tuple[str, str]] = []
    heading = "Overview"
    cursor = 0

    for match in _HEADING.finditer(text):
        body = text[cursor : match.start()].strip()
        if body:
            sections.append((heading, body))
        if match.group(1) == "#" and not title:
            title = match.group(2)
        else:
            heading = match.group(2)
        cursor = match.end()

    body = text[cursor:].strip()
    if body:
        sections.append((heading, body))

    if len(sections) > 1 and sections[0][0] == "Overview":
        intro = sections.pop(0)[1]
        first_heading, first_body = sections[0]
        sections[0] = (first_heading, f"{intro}\n\n{first_body}")
    return title, sections


def _pack(pieces: list[str], limit: int, joiner: str) -> list[str]:
    """Greedily join pieces into groups no longer than `limit` characters."""
    groups: list[str] = []
    current = ""
    for piece in pieces:
        candidate = f"{current}{joiner}{piece}" if current else piece
        if current and len(candidate) > limit:
            groups.append(current)
            current = piece
        else:
            current = candidate
    if current:
        groups.append(current)
    return groups


def _split_long(body: str, limit: int, overlap: int) -> list[str]:
    """
    Cut a section that is too long for one chunk.

    Paragraph breaks first, then sentence ends. Never mid-sentence. When a
    section has to be cut, the last `overlap` characters' worth of whole
    sentences from one piece are repeated at the start of the next, so a
    thought that spans the cut is still readable from either side.
    """
    if len(body) <= limit:
        return [body]

    pieces: list[str] = []
    for paragraph in body.split("\n\n"):
        if len(paragraph) <= limit:
            pieces.append(paragraph)
        else:
            sentences = re.split(r"(?<=[.!?])\s+", paragraph)
            pieces.extend(_pack(sentences, limit, " "))

    groups = _pack(pieces, limit, "\n\n")
    if overlap <= 0:
        return groups

    with_overlap = [groups[0]]
    for previous, group in zip(groups, groups[1:]):
        tail = ""
        for sentence in reversed(re.split(r"(?<=[.!?])\s+", previous)):
            if len(tail) + len(sentence) > overlap:
                break
            tail = f"{sentence} {tail}".strip()
        with_overlap.append(f"{tail}\n\n{group}" if tail else group)
    return with_overlap


def split_documents(documents: list[Document]) -> list[Chunk]:
    """
    One chunk per `## ` section, labelled with the guide and section it is from.

    The city guides are organised by heading: every town guide has the same
    sections (Getting there, Getting around, Eat and drink, ...), and a
    question like "how do I get to Kestrelford?" is answered by exactly one of
    them. Sections run 175 to 710 characters, so a section already is the
    right-sized unit, and the fixed-size fallback was slicing straight through
    them.

    Every chunk starts with "<guide title> > <section heading>". Without it,
    "Getting there" in Kestrelford and "Getting there" in Halden Bay read
    almost the same, and a chunk about bus times would not say which town
    the buses go to.

    A section longer than config.CHUNK_SIZE is cut at paragraph, then
    sentence, boundaries with config.CHUNK_OVERLAP characters of whole
    sentences repeated across the cut. Nothing in city_guides is that long
    today; this is here so a longer guide doesn't silently become one giant
    chunk.
    """
    chunks: list[Chunk] = []
    for doc in documents:
        title, sections = _sections(doc.text)
        title = title or doc.source
        index = 0
        for heading, body in sections:
            label = f"{title} > {heading}"
            for piece in _split_long(body, config.CHUNK_SIZE, config.CHUNK_OVERLAP):
                chunks.append(
                    Chunk(
                        text=f"{label}\n\n{piece}",
                        source=doc.source,
                        index=index,
                        produced_by="chunker.py::split_documents",
                    )
                )
                index += 1
    return chunks


def describe(chunks: list[Chunk]) -> str:
    """A one-line summary, printed after indexing."""
    if not chunks:
        return "0 chunks"
    lengths = [len(c.text) for c in chunks]
    return (
        f"{len(chunks)} chunks, "
        f"{sum(lengths) // len(lengths)} characters on average "
        f"(shortest {min(lengths)}, longest {max(lengths)}), "
        f"produced by {chunks[0].produced_by}"
    )


if __name__ == "__main__":
    from ingest import load_documents

    chunks = split_documents(load_documents())
    print(describe(chunks))
