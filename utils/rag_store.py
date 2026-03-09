# utils/rag_store.py
"""
RAG (Retrieval-Augmented Generation) store for the BI dashboard.

Each successful query interaction (user question → SQL → result summary) is embedded
and stored.  When a new question arrives, the top-k semantically similar past
interactions are fetched and injected into the SQL-generation prompt as dynamic
few-shot examples, giving the LLM richer context.

Vector DB: ChromaDB (persistent, local, no server required)
Embeddings: chromadb default – sentence-transformers all-MiniLM-L6-v2
"""

import hashlib
import json
import os
from typing import Optional

import pandas as pd

# ---------------------------------------------------------------------------
# Lazy import: gracefully degrade if chromadb is not installed
# ---------------------------------------------------------------------------
try:
    import chromadb
    from chromadb.utils import embedding_functions

    _CHROMADB_AVAILABLE = True
except ImportError:  # pragma: no cover
    _CHROMADB_AVAILABLE = False


PERSIST_DIR = os.path.join(os.path.dirname(__file__), "..", "rag_data")


class RAGStore:
    """
    Stores and retrieves past query-SQL-result interactions using ChromaDB.

    * store_interaction()  – call after every successful query execution
    * retrieve_similar()   – call before SQL generation to get few-shot context
    """

    def __init__(self, persist_dir: str = PERSIST_DIR):
        self._available = _CHROMADB_AVAILABLE
        if not self._available:
            print("⚠️  chromadb not installed – RAG context disabled. Run: pip install chromadb")
            return

        os.makedirs(persist_dir, exist_ok=True)
        self._client = chromadb.PersistentClient(path=persist_dir)
        self._ef = embedding_functions.DefaultEmbeddingFunction()

        # One collection that stores ALL interactions (global + per-session)
        self._collection = self._client.get_or_create_collection(
            name="query_interactions",
            embedding_function=self._ef,
            metadata={"hnsw:space": "cosine"},
        )
        print(f"✅ RAG store ready – {self._collection.count()} interactions indexed.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def store_interaction(
        self,
        query: str,
        sql: str,
        df_summary: str,
        session_id: str = "default",
    ) -> None:
        """Embed and persist a successful query interaction."""
        if not self._available:
            return

        # Stable ID: same session + same question → overwrite, not duplicate
        doc_id = hashlib.md5(f"{session_id}:{query.strip().lower()}".encode()).hexdigest()

        self._collection.upsert(
            ids=[doc_id],
            documents=[query],          # text that gets embedded
            metadatas=[
                {
                    "sql": sql,
                    "result_summary": df_summary,
                    "session_id": session_id,
                }
            ],
        )

    def retrieve_similar(
        self,
        query: str,
        n_results: int = 3,
        session_id: Optional[str] = None,
    ) -> list[dict]:
        """
        Return the top-n most semantically similar past interactions.

        If session_id is given, tries session-scoped retrieval first; falls back
        to global search when the session has fewer than n_results stored.
        """
        if not self._available:
            return []

        total = self._collection.count()
        if total == 0:
            return []

        # Session-scoped attempt
        if session_id:
            results = self._safe_query(query, n_results, where={"session_id": session_id})
            if results:
                return results

        # Global fallback
        return self._safe_query(query, min(n_results, total))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _safe_query(
        self,
        query: str,
        n_results: int,
        where: Optional[dict] = None,
    ) -> list[dict]:
        """Run a ChromaDB query and return a normalised list, or [] on error."""
        try:
            kwargs: dict = dict(query_texts=[query], n_results=n_results)
            if where:
                kwargs["where"] = where

            res = self._collection.query(**kwargs)

            interactions = []
            if res and res.get("documents") and res["documents"][0]:
                for i, doc in enumerate(res["documents"][0]):
                    meta = res["metadatas"][0][i]
                    # Skip exact match (distance ≈ 0) – identical question already in history
                    distance = res["distances"][0][i] if res.get("distances") else 1.0
                    if distance < 0.01:
                        continue
                    interactions.append(
                        {
                            "query": doc,
                            "sql": meta.get("sql", ""),
                            "result_summary": meta.get("result_summary", ""),
                        }
                    )
            return interactions
        except Exception as e:
            print(f"⚠️  RAG retrieval error: {e}")
            return []


# ---------------------------------------------------------------------------
# Utility: summarise a DataFrame into a short string for metadata storage
# ---------------------------------------------------------------------------

def summarize_dataframe(df: pd.DataFrame) -> str:
    """Create a compact text summary of a result DataFrame."""
    parts = [f"rows={len(df)}  cols={list(df.columns)}"]
    if not df.empty:
        sample = df.head(2).to_dict(orient="records")
        # Truncate to avoid bloating metadata (ChromaDB limit)
        sample_str = json.dumps(sample, default=str)[:400]
        parts.append(f"sample={sample_str}")
    return " | ".join(parts)


# ---------------------------------------------------------------------------
# Module-level singleton – import this everywhere
# ---------------------------------------------------------------------------
rag_store = RAGStore()
