"""Hybrid RAG engine combining ChromaDB vector search with BM25 keyword search via Reciprocal Rank Fusion."""

import os
import json
import chromadb
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import numpy as np


CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "banking_docs"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def _tokenize(text: str) -> list[str]:
    return [t for t in text.lower().split() if t]


class HybridRAG:
    def __init__(self, chroma_path: str = CHROMA_PATH, collection_name: str = COLLECTION_NAME):
        self.chroma_path = chroma_path
        self.collection_name = collection_name

        self.client = chromadb.PersistentClient(path=chroma_path)
        self.collection = self.client.get_or_create_collection(name=collection_name)
        self.embed_model = SentenceTransformer(EMBED_MODEL)

        self.bm25_index = None
        self.doc_texts: list[str] = []
        self.doc_metadatas: list[dict] = []
        self.doc_ids: list[str] = []

        self._build_bm25_index()

    def _build_bm25_index(self):
        data = self.collection.get()
        docs = data.get("documents") or []
        metas = data.get("metadatas") or []
        ids = data.get("ids") or []

        if not docs:
            self.bm25_index = None
            self.doc_texts = []
            self.doc_metadatas = []
            self.doc_ids = []
            print("[HybridRAG] No documents found in collection — BM25 index not built.")
            return

        self.doc_texts = list(docs)
        self.doc_metadatas = list(metas) if metas else [{} for _ in docs]
        self.doc_ids = list(ids)

        tokenized = [_tokenize(d) for d in self.doc_texts]
        self.bm25_index = BM25Okapi(tokenized)
        print(f"[HybridRAG] BM25 index built over {len(self.doc_texts)} documents.")

    def rebuild_bm25_index(self):
        self._build_bm25_index()

    def vector_search(self, query: str, n_results: int = 5) -> list[dict]:
        embedding = self.embed_model.encode([query]).tolist()
        results = self.collection.query(query_embeddings=embedding, n_results=n_results)

        docs = (results.get("documents") or [[]])[0]
        metas = (results.get("metadatas") or [[]])[0]
        dists = (results.get("distances") or [[]])[0]

        out = []
        for i, text in enumerate(docs):
            meta = metas[i] if i < len(metas) and metas[i] is not None else {}
            out.append({
                "text": text,
                "source": meta.get("source", "unknown"),
                "distance": dists[i] if i < len(dists) else None,
                "rank": i + 1,
            })
        return out

    def bm25_search(self, query: str, n_results: int = 5) -> list[dict]:
        if self.bm25_index is None or not self.doc_texts:
            return []

        tokens = _tokenize(query)
        if not tokens:
            return []

        scores = self.bm25_index.get_scores(tokens)
        top_n = min(n_results, len(scores))
        top_idx = np.argsort(scores)[::-1][:top_n]

        out = []
        for rank, idx in enumerate(top_idx, start=1):
            meta = self.doc_metadatas[idx] if idx < len(self.doc_metadatas) else {}
            meta = meta or {}
            out.append({
                "text": self.doc_texts[idx],
                "source": meta.get("source", "unknown"),
                "bm25_score": float(scores[idx]),
                "rank": rank,
            })
        return out

    def hybrid_search(
        self,
        query: str,
        n_results: int = 5,
        vector_weight: float = 0.7,
        bm25_weight: float = 0.3,
    ) -> list[dict]:
        candidate_count = n_results * 2

        vec_results = self.vector_search(query, n_results=candidate_count)
        bm25_results = self.bm25_search(query, n_results=candidate_count)

        rrf_k = 60
        fused: dict[str, dict] = {}

        for r in vec_results:
            key = r["text"]
            entry = fused.setdefault(key, {
                "text": r["text"],
                "source": r["source"],
                "rrf_score": 0.0,
                "vector_rank": None,
                "bm25_rank": None,
                "vector_distance": None,
                "bm25_score": None,
            })
            entry["vector_rank"] = r["rank"]
            entry["vector_distance"] = r["distance"]
            entry["rrf_score"] += vector_weight * (1.0 / (rrf_k + r["rank"]))

        for r in bm25_results:
            key = r["text"]
            entry = fused.setdefault(key, {
                "text": r["text"],
                "source": r["source"],
                "rrf_score": 0.0,
                "vector_rank": None,
                "bm25_rank": None,
                "vector_distance": None,
                "bm25_score": None,
            })
            entry["bm25_rank"] = r["rank"]
            entry["bm25_score"] = r["bm25_score"]
            if not entry.get("source") or entry["source"] == "unknown":
                entry["source"] = r["source"]
            entry["rrf_score"] += bm25_weight * (1.0 / (rrf_k + r["rank"]))

        ranked = sorted(fused.values(), key=lambda x: x["rrf_score"], reverse=True)
        return ranked[:n_results]

    def compare_methods(self, query: str, n_results: int = 3):
        vec = self.vector_search(query, n_results=n_results)
        bm25 = self.bm25_search(query, n_results=n_results)
        hybrid = self.hybrid_search(query, n_results=n_results)

        divider = "=" * 70

        print(divider)
        print(f"QUERY: {query}")
        print(divider)

        print("\n--- VECTOR SEARCH (ChromaDB) ---")
        if not vec:
            print("(no results)")
        for r in vec:
            print(f"  [{r['rank']}] distance={r['distance']:.4f} | source={r['source']}")
            print(f"      {r['text'][:150]}")

        print("\n--- BM25 SEARCH (Keyword) ---")
        if not bm25:
            print("(no results — BM25 index empty or query has no usable tokens)")
        for r in bm25:
            print(f"  [{r['rank']}] score={r['bm25_score']:.4f} | source={r['source']}")
            print(f"      {r['text'][:150]}")

        print("\n--- HYBRID SEARCH (RRF Fusion) ---")
        if not hybrid:
            print("(no results)")
        for i, r in enumerate(hybrid, start=1):
            found_in = []
            if r["vector_rank"] is not None:
                found_in.append(f"vector#{r['vector_rank']}")
            if r["bm25_rank"] is not None:
                found_in.append(f"bm25#{r['bm25_rank']}")
            tag = ", ".join(found_in) if found_in else "none"
            print(f"  [{i}] rrf={r['rrf_score']:.4f} | found in: {tag} | source={r['source']}")
            print(f"      {r['text'][:150]}")

        print(divider)


if __name__ == "__main__":
    rag = HybridRAG()

    while True:
        print("\n=== HybridRAG ===")
        print("1. Compare search methods")
        print("2. Hybrid search only")
        print("3. Exit")
        choice = input("Choice: ").strip()

        if choice == "3":
            break

        if choice not in {"1", "2"}:
            print("Invalid choice.")
            continue

        query = input("Query: ").strip()
        if not query:
            print("Empty query.")
            continue

        if choice == "1":
            rag.compare_methods(query, n_results=3)
        else:
            results = rag.hybrid_search(query, n_results=5)
            print("\n--- Hybrid Results ---")
            if not results:
                print("(no results)")
            for i, r in enumerate(results, start=1):
                print(f"\n[{i}] rrf_score={r['rrf_score']:.4f} | source={r['source']}")
                print(f"     vector_rank={r['vector_rank']} | bm25_rank={r['bm25_rank']}")
                print(f"     {r['text'][:200]}")
