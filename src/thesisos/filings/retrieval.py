"""Lightweight deterministic TF-IDF and keyword passage retrieval engine."""
import math
import re
from collections import Counter
from typing import List
import numpy as np
from pydantic import BaseModel
from thesisos.data.sources import SourceRecord

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    _HAS_SKLEARN = True
except ImportError:
    _HAS_SKLEARN = False


class RetrievedPassage(BaseModel):
    rank: int
    score: float
    source: SourceRecord


def _pure_python_tfidf_sims(texts: List[str], query: str) -> List[float]:
    """Pure-Python/NumPy TF-IDF cosine similarity fallback if scikit-learn is not installed."""
    tokenize = lambda s: [w.lower() for w in re.findall(r"[a-zA-Z0-9]+", s) if len(w) > 2]
    all_docs = [tokenize(t) for t in texts + [query]]
    n_docs = len(all_docs)
    df_counts = Counter(tok for doc in all_docs for tok in set(doc))
    vocab = sorted(df_counts.keys())
    if not vocab:
        return [0.0] * len(texts)
    tok_to_idx = {t: i for i, t in enumerate(vocab)}
    mat = np.zeros((n_docs, len(vocab)), dtype=float)
    for d_i, doc in enumerate(all_docs):
        tf = Counter(doc)
        for tok, cnt in tf.items():
            idf = math.log((1.0 + n_docs) / (1.0 + df_counts[tok])) + 1.0
            mat[d_i, tok_to_idx[tok]] = cnt * idf
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0.0] = 1.0
    normed = mat / norms
    q_vec = normed[-1]
    doc_vecs = normed[:-1]
    return (doc_vecs @ q_vec).tolist()


def retrieve_relevant_passages(
    query: str,
    corpus: List[SourceRecord],
    top_k: int = 5,
) -> List[RetrievedPassage]:
    """Rank SourceRecords against an analyst query using TF-IDF cosine similarity + keyword boost."""
    if not query.strip() or not corpus:
        return []

    texts = [rec.extracted_passage for rec in corpus]
    if _HAS_SKLEARN:
        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        try:
            tfidf_matrix = vectorizer.fit_transform(texts + [query])
            sims = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).flatten().tolist()
        except ValueError:
            return []
    else:
        sims = _pure_python_tfidf_sims(texts, query)

    # Exact token overlap boost
    q_tokens = {t.lower() for t in query.split() if len(t) > 3}
    boosted_scores = []
    for idx, rec in enumerate(corpus):
        passage_lower = rec.extracted_passage.lower()
        overlap = sum(1 for tok in q_tokens if tok in passage_lower)
        boosted_scores.append(float(sims[idx]) + 0.08 * overlap)

    ranked_indices = np.argsort(boosted_scores)[::-1]
    results: List[RetrievedPassage] = []
    rank_num = 1
    for idx in ranked_indices:
        sc = round(boosted_scores[int(idx)], 4)
        if sc <= 0.0:
            continue
        results.append(RetrievedPassage(rank=rank_num, score=sc, source=corpus[int(idx)]))
        rank_num += 1
        if len(results) >= top_k:
            break
    return results
