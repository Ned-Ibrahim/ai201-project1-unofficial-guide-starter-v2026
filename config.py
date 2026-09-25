"""
Settings for The Unofficial Guide.

Everything you're likely to change lives here, at the top, on purpose.
You'll edit THRESHOLD in Milestone 4 and the chunking numbers in Milestone 3.

Anything you set in your .env file wins over the defaults here.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")


# ─── The corpus you're working with ──────────────────────────────────────────
# Change this to switch corpora, or pass --corpus on the command line.
# Options are the folder names inside corpora/. See corpora/README.md.

CORPUS = os.getenv("AI201_CORPUS", "city_guides")


# ─── Chunking (Milestone 3) ──────────────────────────────────────────────────
# split_documents makes one chunk per `## ` section of a guide. These two
# numbers only matter for a section too long to be one chunk.
#
# city_guides sections run 175 to 710 characters (the longest is the
# "Straightforward" list in guide_accessibility.md), so 900 keeps every
# existing section whole with room for the "Guide > Section" label on top.
# A longer section is cut at sentence ends and repeats up to 150 characters,
# about one sentence in these guides, across the cut.

CHUNK_SIZE = 900        # most characters of body text per chunk
CHUNK_OVERLAP = 150     # whole sentences repeated across a forced cut


# ─── Retrieval (Milestone 4) ─────────────────────────────────────────────────

# 5, not 3: for "which town is easiest with limited mobility?" the chunk that
# names Thornby Wells comes back 4th, behind two Corry Vale chunks that match
# the words "getting around" without answering the question.
TOP_K = 5               # how many chunks to pull back per question

# Unit 2's improvement: rank chunks by keywords (BM25) as well as meaning, and
# merge the two rankings. See store.py::search. False = unit 1's system.
HYBRID = True
# Reciprocal rank fusion constant. 60 is the value from the original RRF paper
# (Cormack et al., 2009) and the common default; it stops one list's rank 1
# from overriding everything the other list says.
RRF_K = 60

# The relevance gate. If the best chunk is further away than this, the system
# refuses to answer instead of handing the model thin material.
#
# LOWER IS BETTER: 0.3 is a close match, 0.9 is unrelated.
#
# Measured on city_guides with split_documents: the five test questions came
# back with best distances 0.234 to 0.641, and the five OUT_OF_SCOPE questions
# 0.840 to 0.997. The starter's 0.6 sat inside the in-corpus group and refused
# "Why do visitors get confused using the buses?" (0.641), which the regional
# transport guide answers. 0.75 sits near the middle of the 0.641 to 0.840 gap,
# about 0.1 clear of each side.
THRESHOLD = 0.75


# ─── Models ──────────────────────────────────────────────────────────────────
# Embeddings run on your own machine and cost no API quota.
# Only generation calls out to a service.

# This is the model Chroma bundles, and leaving it alone is the fast path: it
# downloads about 80 MB from Chroma's own CDN and needs nothing else installed.
#
# Setting it to any other name — unit 2's "try a second embedding model"
# stretch option — switches to loading that model from Hugging Face instead,
# which needs `pip install 'sentence-transformers>=3.4,<3.5'` first. store.py
# says so with a real error message rather than a stack trace if you forget.
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
MODEL = os.getenv("AI201_MODEL", "gemini-3.5-flash-lite")


# ─── Rate limiting and quota guards ──────────────────────────────────────────
# You should not need to touch these. They exist so that a runaway loop costs
# you a warning instead of your whole day's allowance.

# The free tier for gemini-3.5-flash-lite allows 15 requests per minute per
# project (the 429 body says quotaValue '15'). 30 let a 15-question eval run
# straight into the wall. 14 leaves one spare for anything else on the key.
REQUESTS_PER_MINUTE = 14       # outgoing calls the limiter will allow per minute
SESSION_REQUEST_BUDGET = 300   # stop and warn rather than draining the daily quota
MAX_RETRIES = 4                # on 429 / resource-exhausted, with backoff

CACHE_ENABLED = os.getenv("AI201_CACHE", "1") != "0"
CACHE_DIR = ROOT / ".cache"


# ─── Paths ───────────────────────────────────────────────────────────────────

CORPORA_DIR = ROOT / "corpora"
CHROMA_DIR = ROOT / "chroma_db"
RESULTS_DIR = ROOT / "results"


def corpus_path(name: str | None = None) -> Path:
    """Folder holding the documents for a corpus."""
    return CORPORA_DIR / (name or CORPUS) / "documents"


def collection_name(name: str | None = None, variant: str = "default") -> str:
    """
    Name of the vector-store collection for a corpus.

    `variant` lets you index the same corpus two different ways and query both
    without deleting anything — you'll want that in unit 2 when you compare
    chunking strategies.

    Chroma is fussy about collection names: 3 to 63 characters, starting and
    ending with a letter or digit, and nothing but letters, digits, underscores
    and hyphens in between. If you bring your own corpus and name the folder
    something Chroma won't accept, this cleans it up rather than failing.
    """
    import re

    raw = f"{name or CORPUS}__{variant}"
    cleaned = re.sub(r"[^A-Za-z0-9_-]", "-", raw)
    cleaned = cleaned.strip("_-")          # must start and end alphanumeric
    if not cleaned or not cleaned[0].isalnum():
        cleaned = f"c{cleaned}"
    if not cleaned[-1].isalnum():
        cleaned = f"{cleaned}0"
    return cleaned[:63].rstrip("_-") or "collection"
