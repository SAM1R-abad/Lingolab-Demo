"""
Shared spaCy pipeline loading point.

en_core_web_sm is a small (~15 MB) model without word vectors, but with
tokenization/lemmas/POS tags/dependency parsing - enough for vocabulary
and grammar-complexity analysis. This is deliberately not one of the large
transformer models (en_core_web_trf) - those aren't needed here and would
meaningfully slow down analysis of a single submission without a real
benefit for this task.

The model is a process-level singleton: loaded once on first use (normally
inside the Celery worker process), not on every call.
"""

from __future__ import annotations

from functools import lru_cache


@lru_cache(maxsize=1)
def get_nlp():
    import spacy

    return spacy.load("en_core_web_sm")
