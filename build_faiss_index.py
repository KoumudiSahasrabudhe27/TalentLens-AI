"""
build_faiss_index.py

Builds a FAISS index from saved candidate embeddings.
FAISS enables fast similarity search over large embedding collections.
"""

import os
import pickle

import faiss
import numpy as np


PROJECT_ROOT = os.path.dirname(__file__)

EMBEDDINGS_FILE = os.path.join(PROJECT_ROOT, "data", "embeddings", "candidate_embeddings.pkl")
FAISS_INDEX_FILE = os.path.join(PROJECT_ROOT, "data", "embeddings", "candidate_faiss.index")
CANDIDATE_IDS_FILE = os.path.join(PROJECT_ROOT, "data", "embeddings", "candidate_ids.pkl")


def load_embeddings(embeddings_path: str) -> tuple[list, np.ndarray]:
    """
    Load embedding records from pickle and split into IDs and vectors.

    Returns:
        candidate_ids: list of candidate ID strings
        embeddings: numpy array with shape (num_vectors, embedding_dim)
    """
    if not os.path.isfile(embeddings_path):
        raise FileNotFoundError(f"Embeddings file not found: {embeddings_path}")

    with open(embeddings_path, "rb") as input_file:
        embedding_records = pickle.load(input_file)

    if not embedding_records:
        raise ValueError("Embeddings file is empty.")

    candidate_ids = []
    vectors = []

    for record in embedding_records:
        candidate_id = str(record.get("candidate_id", "")).strip()
        embedding = record.get("embedding", [])

        if not candidate_id or not embedding:
            continue

        candidate_ids.append(candidate_id)
        vectors.append(embedding)

    if not vectors:
        raise ValueError("No valid embeddings found in the input file.")

    # Convert Python lists into one numpy float32 matrix for FAISS.
    embeddings = np.array(vectors, dtype=np.float32)
    return candidate_ids, embeddings


def build_faiss_index(embeddings: np.ndarray) -> faiss.IndexFlatIP:
    """
    Build a FAISS inner-product index from embedding vectors.

    IndexFlatIP scores by dot product. After L2 normalization,
    dot product is equivalent to cosine similarity.
    """
    num_vectors, embedding_dim = embeddings.shape

    # IndexFlatIP = exact search using inner product (no training required).
    index = faiss.IndexFlatIP(embedding_dim)

    # Copy vectors so we can normalize in place without changing original data.
    vectors_to_add = embeddings.copy()

    # L2-normalize each vector to unit length.
    faiss.normalize_L2(vectors_to_add)

    # Add all vectors to the index.
    index.add(vectors_to_add)

    return index


def save_index_and_mapping(
    index: faiss.IndexFlatIP,
    candidate_ids: list,
    index_path: str,
    mapping_path: str,
) -> None:
    """Save FAISS index and parallel candidate ID mapping."""
    os.makedirs(os.path.dirname(index_path), exist_ok=True)

    faiss.write_index(index, index_path)

    with open(mapping_path, "wb") as output_file:
        pickle.dump(candidate_ids, output_file)


def format_file_size(size_bytes: int) -> str:
    """Convert bytes to a readable file size string."""
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    return f"{size_bytes / (1024 * 1024):.2f} MB"


def test_similarity_search(
    index: faiss.IndexFlatIP,
    candidate_ids: list,
    embeddings: np.ndarray,
    top_k: int = 5,
) -> None:
    """
    Test the index by searching for neighbors of the first candidate.

    We query with vector 0 and return the top 5 nearest neighbors.
    The first match is usually the query vector itself.
    """
    print("\nSimilarity Search Test (First Candidate)")
    print("-" * 40)

    query_vector = embeddings[0:1].copy()
    faiss.normalize_L2(query_vector)

    query_candidate_id = candidate_ids[0]
    print(f"Query candidate_id: {query_candidate_id}")

    # Search for top_k + 1 so we can still show 5 useful neighbors
    # even when the first result is the query vector itself.
    search_k = min(top_k + 1, index.ntotal)
    similarities, indices = index.search(query_vector, search_k)

    print(f"\nTop {top_k} nearest neighbors:")
    print(f"{'Rank':<6} {'Candidate ID':<16} {'Similarity':>12}")
    print("-" * 36)

    shown = 0
    for neighbor_index, similarity in zip(indices[0], similarities[0]):
        if neighbor_index < 0:
            continue

        neighbor_id = candidate_ids[neighbor_index]

        # Skip the query vector itself when it appears as the top match.
        if neighbor_index == 0:
            continue

        shown += 1
        print(f"{shown:<6} {neighbor_id:<16} {similarity:>12.4f}")

        if shown >= top_k:
            break

    if shown == 0:
        print("No neighbors found.")


if __name__ == "__main__":
    print("=" * 60)
    print("Build FAISS Index")
    print("=" * 60)
    print(f"Input embeddings: {EMBEDDINGS_FILE}")
    print(f"Output index    : {FAISS_INDEX_FILE}")
    print(f"Output IDs      : {CANDIDATE_IDS_FILE}")
    print()

    try:
        # Step 1: Load embeddings from pickle.
        candidate_ids, embeddings = load_embeddings(EMBEDDINGS_FILE)

        num_vectors, embedding_dim = embeddings.shape
        print(f"Loaded {num_vectors:,} embedding vectors.")
        print(f"Embedding dimension: {embedding_dim}")

        # Step 2: Build and save FAISS index + ID mapping.
        index = build_faiss_index(embeddings)
        save_index_and_mapping(
            index,
            candidate_ids,
            FAISS_INDEX_FILE,
            CANDIDATE_IDS_FILE,
        )

        index_size_bytes = os.path.getsize(FAISS_INDEX_FILE)

        print()
        print("=" * 60)
        print("FAISS Index Build Complete")
        print("=" * 60)
        print(f"Number of vectors : {index.ntotal:,}")
        print(f"Embedding dimension: {embedding_dim}")
        print(f"Index file size   : {format_file_size(index_size_bytes)} ({index_size_bytes:,} bytes)")
        print(f"Saved index to    : {FAISS_INDEX_FILE}")
        print(f"Saved ID mapping  : {CANDIDATE_IDS_FILE}")
        print("=" * 60)

        # Step 3: Test similarity search with the first candidate.
        test_similarity_search(index, candidate_ids, embeddings, top_k=5)

    except FileNotFoundError as error:
        print(f"ERROR: {error}")
    except ValueError as error:
        print(f"ERROR: {error}")
    except OSError as error:
        print(f"ERROR: Could not read/write files. {error}")
