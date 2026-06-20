"""
generate_embeddings.py

Generates sentence-transformer embeddings for the top 5000 pre-ranked candidates.
Embeddings turn text summaries into numeric vectors for semantic search.
"""

import csv
import json
import os
import pickle
import time

import numpy as np
from sentence_transformers import SentenceTransformer


# Paths relative to the project root (where this script lives).
PROJECT_ROOT = os.path.dirname(__file__)

TOP_CANDIDATES_FILE = os.path.join(PROJECT_ROOT, "outputs", "top_5000_candidates.csv")
SUMMARIES_FILE = os.path.join(PROJECT_ROOT, "data", "processed", "candidate_summaries.jsonl")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "data", "embeddings", "candidate_embeddings.pkl")

# Hugging Face model used to convert text into embedding vectors.
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Number of summaries encoded at once (batch processing is faster than one-by-one).
BATCH_SIZE = 64


def load_top_candidate_ids(csv_path: str) -> set:
    """
    Load candidate IDs from the top 5000 CSV file.

    We use a set for fast membership checks while scanning summaries.
    """
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"Top candidates file not found: {csv_path}")

    candidate_ids = set()

    with open(csv_path, "r", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            candidate_id = row.get("candidate_id", "").strip()
            if candidate_id:
                candidate_ids.add(candidate_id)

    return candidate_ids


def load_top_candidate_summaries(summaries_path: str, top_candidate_ids: set) -> list:
    """
    Read summaries line-by-line and keep only top 5000 candidates.

    Returns a list of dicts: {"candidate_id": "...", "summary": "..."}
    """
    if not os.path.isfile(summaries_path):
        raise FileNotFoundError(f"Summaries file not found: {summaries_path}")

    matched_records = []

    with open(summaries_path, "r", encoding="utf-8") as summaries_file:
        for line_number, line in enumerate(summaries_file, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON on line {line_number}: {error}"
                ) from error

            candidate_id = str(record.get("candidate_id", "")).strip()
            summary = str(record.get("summary", "")).strip()

            # Keep this record only if the candidate is in the top 5000 set.
            if candidate_id in top_candidate_ids and summary:
                matched_records.append(
                    {
                        "candidate_id": candidate_id,
                        "summary": summary,
                    }
                )

    return matched_records


def generate_embeddings(records: list, model_name: str, batch_size: int) -> list:
    """
    Generate embeddings for all summaries using SentenceTransformer.

    Returns a list of:
      {"candidate_id": "...", "embedding": [float, float, ...]}
    """
    if not records:
        return []

    # Load the pre-trained embedding model.
    model = SentenceTransformer(model_name)

    candidate_ids = [record["candidate_id"] for record in records]
    summaries = [record["summary"] for record in records]

    # encode() runs batch processing internally for speed.
    embedding_vectors = model.encode(
        summaries,
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
    )

    embedding_records = []
    for candidate_id, vector in zip(candidate_ids, embedding_vectors):
        embedding_records.append(
            {
                "candidate_id": candidate_id,
                "embedding": vector.astype(np.float32).tolist(),
            }
        )

    return embedding_records


def save_embeddings(embedding_records: list, output_path: str) -> None:
    """Save embedding records to a pickle file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "wb") as output_file:
        pickle.dump(embedding_records, output_file)


def load_embeddings(input_path: str) -> list:
    """Load embedding records from a pickle file."""
    with open(input_path, "rb") as input_file:
        return pickle.load(input_file)


def test_load_one_embedding(input_path: str) -> None:
    """
    Test section: load one saved embedding and print basic info.

    This confirms the pickle file was written correctly.
    """
    print("\nEmbedding File Test")
    print("-" * 19)

    embedding_records = load_embeddings(input_path)

    if not embedding_records:
        print("No embeddings found in the saved file.")
        return

    first_record = embedding_records[0]
    candidate_id = first_record.get("candidate_id", "N/A")
    embedding = first_record.get("embedding", [])

    print(f"  candidate_id        : {candidate_id}")
    print(f"  embedding dimension : {len(embedding)}")


if __name__ == "__main__":
    print("=" * 60)
    print("Generate Candidate Embeddings")
    print("=" * 60)
    print(f"Model     : {MODEL_NAME}")
    print(f"Top CSV   : {TOP_CANDIDATES_FILE}")
    print(f"Summaries : {SUMMARIES_FILE}")
    print(f"Output    : {OUTPUT_FILE}")
    print(f"Batch size: {BATCH_SIZE}")
    print()

    start_time = time.perf_counter()

    try:
        # Step 1: Load top 5000 candidate IDs from CSV.
        top_candidate_ids = load_top_candidate_ids(TOP_CANDIDATES_FILE)
        print(f"Loaded {len(top_candidate_ids):,} candidate IDs from top 5000 CSV.")

        # Step 2: Read summaries line-by-line and keep only top 5000 matches.
        summary_records = load_top_candidate_summaries(
            SUMMARIES_FILE, top_candidate_ids
        )
        print(f"Matched {len(summary_records):,} summaries for top candidates.")

        if len(summary_records) < len(top_candidate_ids):
            missing_count = len(top_candidate_ids) - len(summary_records)
            print(
                f"Warning: {missing_count:,} top candidates did not have summaries."
            )

        # Step 3: Generate embeddings in batches.
        embedding_records = generate_embeddings(
            summary_records,
            model_name=MODEL_NAME,
            batch_size=BATCH_SIZE,
        )

        # Step 4: Save embeddings to pickle file.
        save_embeddings(embedding_records, OUTPUT_FILE)

        end_time = time.perf_counter()
        elapsed_seconds = end_time - start_time

        # Embedding dimension from the first record (all vectors share same size).
        embedding_dimension = 0
        if embedding_records:
            embedding_dimension = len(embedding_records[0]["embedding"])

        print()
        print("=" * 60)
        print("Embedding Generation Complete")
        print("=" * 60)
        print(f"Embeddings generated : {len(embedding_records):,}")
        print(f"Embedding dimension  : {embedding_dimension}")
        print(f"Runtime              : {elapsed_seconds:.2f} seconds")
        print(f"Saved to             : {OUTPUT_FILE}")
        print("=" * 60)

        # Step 5: Test loading one embedding from the saved file.
        test_load_one_embedding(OUTPUT_FILE)

    except FileNotFoundError as error:
        print(f"ERROR: {error}")
    except ValueError as error:
        print(f"ERROR: {error}")
    except OSError as error:
        print(f"ERROR: Could not read/write files. {error}")
