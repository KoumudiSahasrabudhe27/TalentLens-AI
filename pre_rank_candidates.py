"""
pre_rank_candidates.py

Processes all candidates and builds a preliminary ranking using Talent Score
and Domain Fit Score. Reads the input file line-by-line for efficiency.
"""

import csv
import json
import os
import sys
import time


# Add src/ to Python's import path so we can reuse scoring modules.
PROJECT_ROOT = os.path.dirname(__file__)
SRC_PATH = os.path.join(PROJECT_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from ranking.domain_fit_score import calculate_domain_fit
from ranking.talent_score import calculate_talent_score


# Input: full raw candidate dataset (one JSON object per line).
INPUT_FILE = os.path.join(PROJECT_ROOT, "data", "raw", "candidates.jsonl")

# Output: top 5000 pre-ranked candidates as a CSV file.
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "outputs", "top_5000_candidates.csv")

# Show progress after this many candidates.
PROGRESS_INTERVAL = 5_000

# How many top candidates to save to CSV.
TOP_N = 5_000

# Weights for the preliminary ranking formula.
DOMAIN_FIT_WEIGHT = 0.6
TALENT_SCORE_WEIGHT = 0.4


def process_candidates(input_path: str) -> list:
    """
    Read candidates line-by-line and compute scores for each one.

    Returns a list of ranking records (one dict per candidate).
    """
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    ranking_records = []
    total_processed = 0

    with open(input_path, "r", encoding="utf-8") as input_file:
        for line_number, line in enumerate(input_file, start=1):
            line = line.strip()
            if not line:
                continue

            # Parse one candidate from the current line.
            try:
                candidate = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON on line {line_number}: {error}"
                ) from error

            # Read basic profile fields for the output table.
            profile = candidate.get("profile", {})
            if not isinstance(profile, dict):
                profile = {}

            candidate_id = str(candidate.get("candidate_id", ""))
            current_title = str(profile.get("current_title", ""))

            # Calculate both component scores.
            talent_result = calculate_talent_score(candidate)
            domain_result = calculate_domain_fit(candidate)

            talent_score = float(talent_result.get("talent_score", 0.0) or 0.0)
            domain_fit_score = float(domain_result.get("domain_fit_score", 0.0) or 0.0)

            # Combine scores into one preliminary rank score.
            # Domain fit matters slightly more for this Senior AI Engineer use case.
            pre_rank_score = (
                DOMAIN_FIT_WEIGHT * domain_fit_score
                + TALENT_SCORE_WEIGHT * talent_score
            )
            pre_rank_score = round(pre_rank_score, 2)

            # Store only the fields we need for ranking and export.
            ranking_records.append(
                {
                    "candidate_id": candidate_id,
                    "current_title": current_title,
                    "pre_rank_score": pre_rank_score,
                    "domain_fit_score": round(domain_fit_score, 2),
                    "talent_score": round(talent_score, 2),
                }
            )

            total_processed += 1

            # Print progress every 5,000 candidates.
            if total_processed % PROGRESS_INTERVAL == 0:
                print(f"Processed {total_processed:,} candidates...")

    return ranking_records


def save_top_candidates(records: list, output_path: str, top_n: int) -> list:
    """
    Sort candidates by pre_rank_score (highest first) and save top N to CSV.

    Returns the top N records (used for printing the top 10).
    """
    # Sort descending: highest pre_rank_score first.
    sorted_records = sorted(
        records,
        key=lambda row: row["pre_rank_score"],
        reverse=True,
    )

    top_records = sorted_records[:top_n]

    # Ensure output folder exists.
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Write the top candidates to CSV.
    fieldnames = [
        "candidate_id",
        "current_title",
        "pre_rank_score",
        "domain_fit_score",
        "talent_score",
    ]

    with open(output_path, "w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(top_records)

    return top_records


def print_top_5000_stats(top_records: list) -> None:
    """Print highest, lowest, and average pre_rank_score in the top 5000."""
    if not top_records:
        print("\nNo candidates in top 5000 to summarize.")
        return

    scores = [record["pre_rank_score"] for record in top_records]
    highest_score = max(scores)
    lowest_score = min(scores)
    average_score = sum(scores) / len(scores)

    print("\nTop 5000 Score Summary")
    print("-" * 24)
    print(f"  Highest score : {highest_score:.2f}")
    print(f"  Lowest score  : {lowest_score:.2f}")
    print(f"  Average score : {average_score:.2f}")


def print_top_10(top_records: list) -> None:
    """Print the top 10 candidates in a readable table."""
    print("\nTop 10 Candidates")
    print("-" * 80)
    print(
        f"{'Rank':<5} {'Candidate ID':<16} {'Pre-Rank':>9} "
        f"{'Domain':>8} {'Talent':>8}  Title"
    )
    print("-" * 80)

    for index, record in enumerate(top_records[:10], start=1):
        print(
            f"{index:<5} "
            f"{record['candidate_id']:<16} "
            f"{record['pre_rank_score']:>9.2f} "
            f"{record['domain_fit_score']:>8.2f} "
            f"{record['talent_score']:>8.2f}  "
            f"{record['current_title']}"
        )


if __name__ == "__main__":
    print("=" * 80)
    print("Pre-Rank Candidates")
    print("=" * 80)
    print(f"Input : {INPUT_FILE}")
    print(f"Output: {OUTPUT_FILE}")
    print(
        f"Formula: pre_rank_score = "
        f"({DOMAIN_FIT_WEIGHT} * domain_fit_score) + "
        f"({TALENT_SCORE_WEIGHT} * talent_score)"
    )
    print()

    start_time = time.perf_counter()

    try:
        ranking_records = process_candidates(INPUT_FILE)
        total_processed = len(ranking_records)

        top_records = save_top_candidates(ranking_records, OUTPUT_FILE, TOP_N)

        end_time = time.perf_counter()
        elapsed_seconds = end_time - start_time

        print()
        print("=" * 80)
        print("Pre-Ranking Complete")
        print("=" * 80)
        print(f"Total processed : {total_processed:,}")
        print(f"Top saved       : {len(top_records):,} candidates")
        print(f"Output file     : {OUTPUT_FILE}")
        print(f"Runtime         : {elapsed_seconds:.2f} seconds")

        if total_processed > 0:
            rate = total_processed / elapsed_seconds
            print(f"Processing rate : {rate:,.0f} candidates/second")

        print_top_5000_stats(top_records)
        print_top_10(top_records)
        print("=" * 80)

    except FileNotFoundError as error:
        print(f"ERROR: {error}")
    except ValueError as error:
        print(f"ERROR: {error}")
    except OSError as error:
        print(f"ERROR: Could not read/write files. {error}")
