"""
generate_all_summaries.py

Generates one semantic-search-ready summary per candidate.
Reads and writes line-by-line so we never load all 100,000 records at once.
"""

import json
import os
import sys
import time


# Add src/ to Python's import path so we can reuse project modules.
PROJECT_ROOT = os.path.dirname(__file__)
SRC_PATH = os.path.join(PROJECT_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from reasoning.candidate_summary import generate_candidate_summary


# Input: raw candidate profiles (one JSON object per line).
INPUT_FILE = os.path.join(PROJECT_ROOT, "data", "raw", "candidates.jsonl")

# Output: processed summaries ready for semantic search / embeddings.
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "data", "processed", "candidate_summaries.jsonl")

# Show progress after this many candidates.
PROGRESS_INTERVAL = 5_000


def format_file_size(size_bytes: int) -> str:
    """Convert bytes into a human-readable file size string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    if size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def generate_all_summaries(input_path: str, output_path: str) -> int:
    """
    Read candidates line-by-line, generate summaries, and write JSONL output.

    Returns the number of candidates successfully processed.
    """
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Make sure the output folder exists before we start writing.
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    total_processed = 0

    # Open input and output files at the same time.
    # We read one candidate, write one summary, then move to the next line.
    with open(input_path, "r", encoding="utf-8") as input_file, open(
        output_path, "w", encoding="utf-8"
    ) as output_file:
        for line_number, line in enumerate(input_file, start=1):
            line = line.strip()
            if not line:
                continue

            # Parse one candidate record from the current line.
            try:
                candidate = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON on line {line_number}: {error}"
                ) from error

            # Reuse the shared summary function from candidate_summary.py.
            candidate_id = str(candidate.get("candidate_id", ""))
            summary = generate_candidate_summary(candidate)

            # Build the output record for semantic search pipelines.
            output_record = {
                "candidate_id": candidate_id,
                "summary": summary,
            }

            # json.dumps converts a Python dict to a JSON string.
            # We add "\n" so each record is on its own line (JSONL format).
            output_file.write(json.dumps(output_record, ensure_ascii=False) + "\n")

            total_processed += 1

            # Print progress every 5,000 candidates.
            if total_processed % PROGRESS_INTERVAL == 0:
                print(f"Processed {total_processed:,} candidates...")

    return total_processed


if __name__ == "__main__":
    print("=" * 60)
    print("Generating Candidate Summaries")
    print("=" * 60)
    print(f"Input : {INPUT_FILE}")
    print(f"Output: {OUTPUT_FILE}")
    print()

    # Record start time for performance reporting.
    start_time = time.perf_counter()

    try:
        total_processed = generate_all_summaries(INPUT_FILE, OUTPUT_FILE)

        # Record end time after all summaries are written.
        end_time = time.perf_counter()
        elapsed_seconds = end_time - start_time

        # Get the final output file size from disk.
        output_size_bytes = os.path.getsize(OUTPUT_FILE)

        print()
        print("=" * 60)
        print("Summary Generation Complete")
        print("=" * 60)
        print(f"Total processed : {total_processed:,}")
        print(f"Output file     : {OUTPUT_FILE}")
        print(f"Output file size: {format_file_size(output_size_bytes)} ({output_size_bytes:,} bytes)")
        print(f"Elapsed time    : {elapsed_seconds:.2f} seconds")
        if total_processed > 0:
            rate = total_processed / elapsed_seconds
            print(f"Processing rate : {rate:,.0f} candidates/second")
        print("=" * 60)

    except FileNotFoundError as error:
        print(f"ERROR: {error}")
    except ValueError as error:
        print(f"ERROR: {error}")
    except OSError as error:
        print(f"ERROR: Could not read/write files. {error}")
