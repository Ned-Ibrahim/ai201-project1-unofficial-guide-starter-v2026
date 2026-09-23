"""
Stage 1 of the pipeline: loading documents off disk and cleaning them up.

The five stages are loading, chunking, embedding, retrieval, and generation.
When something goes wrong in unit 2, your job is to work out which of the five
it happened in. This is the first one.
"""

import re
from dataclasses import dataclass
from pathlib import Path

import config


@dataclass
class Document:
    """One source file, cleaned and ready to be chunked."""

    source: str   # the filename, e.g. "housing_lottery.txt" — this is what gets cited
    text: str


def clean_text(raw: str) -> str:
    """
    Strip the stuff that isn't the real content.

    Provided corpora are already fairly clean. If you bring your own documents
    — especially anything scraped from a web page — this is where navigation
    text, ads, cookie banners and repeated boilerplate come out.
    """
    text = raw.replace("\r\n", "\n").replace("\r", "\n")

    # Collapse runs of blank lines down to one.
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Collapse repeated spaces and tabs, but keep line structure intact.
    text = re.sub(r"[ \t]{2,}", " ", text)

    # Markdown bold/italic markers are formatting, not content.
    text = re.sub(r"\*{1,2}([^*\n]+)\*{1,2}", r"\1", text)

    return _unwrap(text).strip()


def _is_structural(line: str) -> bool:
    """Headings, list items, quotes and thread markers keep their own line."""
    stripped = line.strip()
    return (
        not stripped
        or stripped.startswith(("#", "-", "*", ">", "|"))
        or stripped.endswith("---")
        or re.match(r"^\d+\. ", stripped) is not None
    )


def _unwrap(text: str) -> str:
    """
    Join hard-wrapped prose lines back into one line per paragraph.

    Some guides wrap at 80 columns and some don't, so the same kind of
    paragraph would otherwise show up in chunks looking two different ways.
    """
    out: list[str] = []
    for line in text.split("\n"):
        if out and not _is_structural(out[-1]) and not _is_structural(line):
            out[-1] = f"{out[-1]} {line.strip()}"
        else:
            out.append(line)
    return "\n".join(out)


# A section whose body appears word for word in this many documents is a
# template the corpus author pasted everywhere, not information about any one
# place. In city_guides every town guide ends with the same "Practical notes"
# paragraph, which even names Brightwater as the nearest hospital inside the
# Brightwater and Marchwood guides.
BOILERPLATE_MIN_DOCS = 3

_SECTION = re.compile(r"(?ms)^## [^\n]*\n+(.*?)(?=^## |\Z)")


def strip_repeated_sections(documents: list["Document"]) -> list["Document"]:
    """Drop any `## ` section whose body is repeated across many documents."""
    seen: dict[str, int] = {}
    for doc in documents:
        for body in {m.group(1).strip() for m in _SECTION.finditer(doc.text)}:
            seen[body] = seen.get(body, 0) + 1

    repeated = {body for body, count in seen.items() if count >= BOILERPLATE_MIN_DOCS}
    if not repeated:
        return documents

    cleaned = []
    for doc in documents:
        text = _SECTION.sub(
            lambda m: "" if m.group(1).strip() in repeated else m.group(0),
            doc.text,
        )
        cleaned.append(Document(source=doc.source, text=text.strip()))
    return cleaned


def load_documents(corpus: str | None = None) -> list[Document]:
    """
    Read every .txt and .md file in the corpus folder.

    Returns a list of Documents. Each one keeps its filename, because every
    answer your system produces has to name the document it came from.
    """
    folder = config.corpus_path(corpus)

    if not folder.exists():
        raise FileNotFoundError(
            f"No corpus at {folder}.\n"
            f"Check the corpus name in config.py, or see corpora/README.md "
            f"for what's available."
        )

    documents: list[Document] = []
    for path in sorted(folder.iterdir()):
        if path.suffix.lower() not in {".txt", ".md"}:
            continue
        text = clean_text(path.read_text(encoding="utf-8"))
        if text:
            documents.append(Document(source=path.name, text=text))

    if not documents:
        raise ValueError(f"{folder} has no .txt or .md files in it.")

    return strip_repeated_sections(documents)


def describe(documents: list[Document]) -> str:
    """A one-line summary, printed after indexing so you can sanity-check it."""
    total = sum(len(d.text) for d in documents)
    avg = total // max(len(documents), 1)
    return (
        f"{len(documents)} documents, "
        f"{total:,} characters, "
        f"~{avg:,} characters per document"
    )


if __name__ == "__main__":
    docs = load_documents()
    print(describe(docs))
    print()
    for doc in docs[:3]:
        preview = doc.text[:200].replace("\n", " ")
        print(f"  {doc.source}: {preview}...")
