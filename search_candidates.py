"""
search_candidates.py

Searches the top 5000 candidates using semantic similarity to the job description.
Uses a FAISS index built from candidate summary embeddings.
"""

import csv
import os
import pickle

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


PROJECT_ROOT = os.path.dirname(__file__)

# Files used for search and result enrichment.
FAISS_INDEX_FILE = os.path.join(PROJECT_ROOT, "data", "embeddings", "candidate_faiss.index")
CANDIDATE_IDS_FILE = os.path.join(PROJECT_ROOT, "data", "embeddings", "candidate_ids.pkl")
EMBEDDINGS_FILE = os.path.join(PROJECT_ROOT, "data", "embeddings", "candidate_embeddings.pkl")
SUMMARIES_FILE = os.path.join(PROJECT_ROOT, "data", "processed", "candidate_summaries.jsonl")
TOP_CANDIDATES_FILE = os.path.join(PROJECT_ROOT, "outputs", "top_5000_candidates.csv")

JOB_DESCRIPTION_FILE = os.path.join(PROJECT_ROOT, "data", "raw", "job_description.txt")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "outputs", "top_20_semantic_matches.csv")

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K = 20


def verify_input_files() -> None:
    """Confirm all required pipeline files exist before searching."""
    required_files = [
        FAISS_INDEX_FILE,
        CANDIDATE_IDS_FILE,
        EMBEDDINGS_FILE,
        SUMMARIES_FILE,
        TOP_CANDIDATES_FILE,
        JOB_DESCRIPTION_FILE,
    ]

    for file_path in required_files:
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"Required input file not found: {file_path}")


def load_faiss_index(index_path: str) -> faiss.Index:
    """Load a saved FAISS index from disk."""
    if not os.path.isfile(index_path):
        raise FileNotFoundError(f"FAISS index not found: {index_path}")

    return faiss.read_index(index_path)


def load_candidate_ids(mapping_path: str) -> list:
    """
    Load candidate ID mapping.

    Index position i in FAISS corresponds to candidate_ids[i].
    """
    if not os.path.isfile(mapping_path):
        raise FileNotFoundError(f"Candidate ID mapping not found: {mapping_path}")

    with open(mapping_path, "rb") as input_file:
        return pickle.load(input_file)


def load_candidate_metadata(csv_path: str) -> dict:
    """
    Load current_title and pre_rank_score for each candidate.

    Returns a dictionary keyed by candidate_id.
    """
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"Top candidates file not found: {csv_path}")

    metadata = {}

    with open(csv_path, "r", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            candidate_id = row.get("candidate_id", "").strip()
            if not candidate_id:
                continue

            metadata[candidate_id] = {
                "current_title": row.get("current_title", ""),
                "pre_rank_score": float(row.get("pre_rank_score", 0.0) or 0.0),
            }

    return metadata


def read_job_description(job_description_path: str) -> str:
    """Read the full job description text from a .txt file."""
    if not os.path.isfile(job_description_path):
        raise FileNotFoundError(f"Job description not found: {job_description_path}")

    with open(job_description_path, "r", encoding="utf-8") as job_file:
        job_text = job_file.read().strip()

    if not job_text:
        raise ValueError(f"Job description file is empty: {job_description_path}")

    return job_text


def generate_job_description_embedding(job_text: str, model_name: str) -> np.ndarray:
    """
    Convert the job description into one embedding vector.

    Uses the same model that created candidate embeddings.
    """
    model = SentenceTransformer(model_name)

    # encode returns a 1D numpy array for a single text input.
    embedding = model.encode(job_text, convert_to_numpy=True)

    # FAISS expects shape (1, embedding_dim) for search queries.
    return np.array([embedding], dtype=np.float32)


def search_candidates(
    index: faiss.Index,
    candidate_ids: list,
    query_embedding: np.ndarray,
    top_k: int,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Search FAISS for the most similar candidate vectors.

    Returns:
        similarities: similarity score for each match
        indices: FAISS index positions for each match
    """
    # Normalize query vector so inner product equals cosine similarity.
    query_vector = query_embedding.copy()
    faiss.normalize_L2(query_vector)

    # search returns scores and index positions for top_k neighbors.
    similarities, indices = index.search(query_vector, top_k)
    return similarities[0], indices[0]


def build_search_results(
    similarities: np.ndarray,
    indices: np.ndarray,
    candidate_ids: list,
    metadata: dict,
) -> list:
    """Combine FAISS search output with candidate metadata."""
    results = []

    for similarity, faiss_index in zip(similarities, indices):
        if faiss_index < 0:
            continue

        candidate_id = candidate_ids[faiss_index]
        candidate_meta = metadata.get(candidate_id, {})

        results.append(
            {
                "candidate_id": candidate_id,
                "similarity_score": round(float(similarity), 4),
                "current_title": candidate_meta.get("current_title", "N/A"),
                "pre_rank_score": round(
                    float(candidate_meta.get("pre_rank_score", 0.0) or 0.0), 2
                ),
            }
        )

    return results


def save_results(results: list, output_path: str) -> None:
    """Save top semantic matches to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fieldnames = [
        "candidate_id",
        "similarity_score",
        "current_title",
        "pre_rank_score",
    ]

    with open(output_path, "w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


def print_leaderboard(results: list) -> None:
    """Print a readable leaderboard table in the terminal."""
    print("\nTop 20 Semantic Matches")
    print("-" * 88)
    print(
        f"{'Rank':<5} {'Candidate ID':<16} {'Similarity':>10} "
        f"{'Pre-Rank':>10}  Title"
    )
    print("-" * 88)

    for rank, result in enumerate(results, start=1):
        print(
            f"{rank:<5} "
            f"{result['candidate_id']:<16} "
            f"{result['similarity_score']:>10.4f} "
            f"{result['pre_rank_score']:>10.2f}  "
            f"{result['current_title']}"
        )


if __name__ == "__main__":
    print("=" * 88)
    print("Semantic Candidate Search")
    print("=" * 88)
    print(f"Model           : {MODEL_NAME}")
    print(f"FAISS index     : {FAISS_INDEX_FILE}")
    print(f"Candidate IDs   : {CANDIDATE_IDS_FILE}")
    print(f"Embeddings file : {EMBEDDINGS_FILE}")
    print(f"Summaries file  : {SUMMARIES_FILE}")
    print(f"Top 5000 CSV    : {TOP_CANDIDATES_FILE}")
    print(f"Job description : {JOB_DESCRIPTION_FILE}")
    print(f"Output CSV      : {OUTPUT_FILE}")
    print()

    try:
        # Confirm all listed input files exist (we do not load summaries/embeddings into memory).
        verify_input_files()

        # Step 1: Load FAISS index.
        index = load_faiss_index(FAISS_INDEX_FILE)
        print(f"Loaded FAISS index with {index.ntotal:,} vectors.")

        # Step 2: Load candidate ID mapping (index position -> candidate_id).
        candidate_ids = load_candidate_ids(CANDIDATE_IDS_FILE)
        print(f"Loaded {len(candidate_ids):,} candidate IDs.")

        # Step 3: Load metadata (title + pre-rank score) for result enrichment.
        candidate_metadata = load_candidate_metadata(TOP_CANDIDATES_FILE)
        print(f"Loaded metadata for {len(candidate_metadata):,} candidates.")

        # Step 4: Read the job description text.
        job_description = read_job_description(JOB_DESCRIPTION_FILE)
        print(f"Loaded job description ({len(job_description):,} characters).")

        # Step 5: Generate and normalize a JD embedding.
        jd_embedding = generate_job_description_embedding(job_description, MODEL_NAME)
        print(f"Generated JD embedding with dimension {jd_embedding.shape[1]}.")

        # Step 6: Search FAISS for top matches.
        similarities, indices = search_candidates(
            index,
            candidate_ids,
            jd_embedding,
            top_k=TOP_K,
        )

        # Step 7: Build final result rows.
        results = build_search_results(
            similarities,
            indices,
            candidate_ids,
            candidate_metadata,
        )

        # Step 8: Save and print results.
        save_results(results, OUTPUT_FILE)
        print_leaderboard(results)

        print()
        print(f"Saved results to: {OUTPUT_FILE}")
        print("=" * 88)

    except FileNotFoundError as error:
        print(f"ERROR: {error}")
    except ValueError as error:
        print(f"ERROR: {error}")
    except OSError as error:
        print(f"ERROR: Could not read/write files. {error}")
