"""
search_candidates_v2.py

Searches candidates using a focused semantic query from search_query.txt.
This version uses a shorter, JD-derived query instead of the full job description.
"""

import csv
import os
import pickle
import time

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


PROJECT_ROOT = os.path.dirname(__file__)

FAISS_INDEX_FILE = os.path.join(PROJECT_ROOT, "data", "embeddings", "candidate_faiss.index")
CANDIDATE_IDS_FILE = os.path.join(PROJECT_ROOT, "data", "embeddings", "candidate_ids.pkl")
SEARCH_QUERY_FILE = os.path.join(PROJECT_ROOT, "outputs", "search_query.txt")
TOP_CANDIDATES_FILE = os.path.join(PROJECT_ROOT, "outputs", "top_5000_candidates.csv")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "outputs", "top_100_semantic_v2.csv")

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K = 100
LEADERBOARD_SIZE = 20


def _safe_float(value, default: float = 0.0) -> float:
    """Convert a CSV value to float safely."""
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def verify_input_files() -> None:
    """Confirm required input files exist before searching."""
    required_files = [
        FAISS_INDEX_FILE,
        CANDIDATE_IDS_FILE,
        SEARCH_QUERY_FILE,
        TOP_CANDIDATES_FILE,
    ]

    for file_path in required_files:
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"Required input file not found: {file_path}")


def load_faiss_index(index_path: str) -> faiss.Index:
    """Load a saved FAISS index from disk."""
    return faiss.read_index(index_path)


def load_candidate_ids(mapping_path: str) -> list:
    """
    Load candidate ID mapping.

    FAISS index position i maps to candidate_ids[i].
    """
    with open(mapping_path, "rb") as input_file:
        return pickle.load(input_file)


def load_candidate_metadata(csv_path: str) -> dict:
    """
    Load candidate metadata from top_5000_candidates.csv.

    Returns a dictionary keyed by candidate_id.
    """
    metadata = {}

    with open(csv_path, "r", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            candidate_id = row.get("candidate_id", "").strip()
            if not candidate_id:
                continue

            metadata[candidate_id] = {
                "current_title": row.get("current_title", "").strip(),
                "pre_rank_score": _safe_float(row.get("pre_rank_score")),
                "domain_fit_score": _safe_float(row.get("domain_fit_score")),
                "talent_score": _safe_float(row.get("talent_score")),
            }

    return metadata


def read_search_query(query_path: str) -> str:
    """Load the semantic search query from search_query.txt."""
    with open(query_path, "r", encoding="utf-8") as query_file:
        query_text = query_file.read().strip()

    if not query_text:
        raise ValueError(f"Search query file is empty: {query_path}")

    return query_text


def generate_query_embedding(query_text: str, model_name: str) -> np.ndarray:
    """
    Convert the search query into one embedding vector.

    Uses the same model that created candidate embeddings.
    """
    model = SentenceTransformer(model_name)
    embedding = model.encode(query_text, convert_to_numpy=True)

    # FAISS expects shape (1, embedding_dim) for a single query.
    return np.array([embedding], dtype=np.float32)


def search_faiss(index: faiss.Index, query_embedding: np.ndarray, top_k: int):
    """
    Search FAISS for the most similar candidate vectors.

    Returns similarity scores and FAISS index positions.
    """
    query_vector = query_embedding.copy()

    # Normalize so inner product equals cosine similarity.
    faiss.normalize_L2(query_vector)

    similarities, indices = index.search(query_vector, top_k)
    return similarities[0], indices[0]


def build_search_results(
    similarities: np.ndarray,
    indices: np.ndarray,
    candidate_ids: list,
    metadata: dict,
) -> list:
    """Join FAISS search results with candidate metadata from CSV."""
    results = []

    for similarity, faiss_index in zip(similarities, indices):
        if faiss_index < 0:
            continue

        candidate_id = candidate_ids[faiss_index]
        candidate_meta = metadata.get(candidate_id, {})

        results.append(
            {
                "candidate_id": candidate_id,
                "current_title": candidate_meta.get("current_title", "N/A"),
                "similarity_score": round(float(similarity), 4),
                "pre_rank_score": round(
                    float(candidate_meta.get("pre_rank_score", 0.0) or 0.0), 2
                ),
                "domain_fit_score": round(
                    float(candidate_meta.get("domain_fit_score", 0.0) or 0.0), 2
                ),
                "talent_score": round(
                    float(candidate_meta.get("talent_score", 0.0) or 0.0), 2
                ),
            }
        )

    return results


def save_results(results: list, output_path: str) -> None:
    """Save semantic search results to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fieldnames = [
        "candidate_id",
        "current_title",
        "similarity_score",
        "pre_rank_score",
        "domain_fit_score",
        "talent_score",
    ]

    with open(output_path, "w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


def print_leaderboard(results: list, top_n: int = LEADERBOARD_SIZE) -> None:
    """Print top N candidates in a simple leaderboard table."""
    print(f"\nTop {top_n} Leaderboard")
    print("-" * 72)
    print(f"{'Rank':<6} {'Candidate ID':<16} {'Similarity':>12}  Title")
    print("-" * 72)

    for rank, result in enumerate(results[:top_n], start=1):
        print(
            f"{rank:<6} "
            f"{result['candidate_id']:<16} "
            f"{result['similarity_score']:>12.4f}  "
            f"{result['current_title']}"
        )


if __name__ == "__main__":
    print("=" * 72)
    print("Semantic Candidate Search v2")
    print("=" * 72)
    print(f"Model         : {MODEL_NAME}")
    print(f"FAISS index   : {FAISS_INDEX_FILE}")
    print(f"Candidate IDs : {CANDIDATE_IDS_FILE}")
    print(f"Search query  : {SEARCH_QUERY_FILE}")
    print(f"Top 5000 CSV  : {TOP_CANDIDATES_FILE}")
    print(f"Output CSV    : {OUTPUT_FILE}")
    print()

    start_time = time.perf_counter()

    try:
        verify_input_files()

        # Step 1: Load FAISS index and candidate ID mapping.
        index = load_faiss_index(FAISS_INDEX_FILE)
        candidate_ids = load_candidate_ids(CANDIDATE_IDS_FILE)
        print(f"Loaded FAISS index with {index.ntotal:,} vectors.")

        # Step 2: Load candidate metadata for joining results.
        candidate_metadata = load_candidate_metadata(TOP_CANDIDATES_FILE)
        print(f"Loaded metadata for {len(candidate_metadata):,} candidates.")

        # Step 3: Load the focused semantic search query.
        search_query = read_search_query(SEARCH_QUERY_FILE)
        print(f"Loaded search query ({len(search_query)} characters).")

        # Step 4: Generate and normalize query embedding.
        query_embedding = generate_query_embedding(search_query, MODEL_NAME)
        print(f"Generated query embedding with dimension {query_embedding.shape[1]}.")

        # Step 5: Search FAISS for top 100 matches.
        similarities, indices = search_faiss(index, query_embedding, top_k=TOP_K)

        # Step 6: Join search results with CSV metadata.
        results = build_search_results(
            similarities,
            indices,
            candidate_ids,
            candidate_metadata,
        )

        # Step 7: Save full top 100 results.
        save_results(results, OUTPUT_FILE)

        end_time = time.perf_counter()
        elapsed_seconds = end_time - start_time

        # Step 8: Print top 20 leaderboard and runtime.
        print_leaderboard(results, top_n=LEADERBOARD_SIZE)

        print()
        print(f"Saved {len(results)} results to: {OUTPUT_FILE}")
        print(f"Runtime: {elapsed_seconds:.2f} seconds")
        print("=" * 72)

    except FileNotFoundError as error:
        print(f"ERROR: {error}")
    except ValueError as error:
        print(f"ERROR: {error}")
    except OSError as error:
        print(f"ERROR: Could not read/write files. {error}")
