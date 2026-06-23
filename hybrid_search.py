"""
hybrid_search.py

Combines semantic similarity, domain fit, and talent score into one final ranking.
This hybrid approach balances JD relevance with candidate quality signals.
"""

import csv
import os
import time


PROJECT_ROOT = os.path.dirname(__file__)

TOP_5000_FILE = os.path.join(PROJECT_ROOT, "outputs", "top_5000_candidates.csv")
SEMANTIC_MATCHES_FILE = os.path.join(
    PROJECT_ROOT, "outputs", "top_20_semantic_matches.csv"
)
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "outputs", "top_20_hybrid_ranked.csv")

# Weights used in the final hybrid score formula.
SIMILARITY_WEIGHT = 0.50
DOMAIN_FIT_WEIGHT = 0.30
TALENT_SCORE_WEIGHT = 0.20


def _safe_float(value, default: float = 0.0) -> float:
    """Convert a CSV value to float safely."""
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def load_top_5000_lookup(csv_path: str) -> dict:
    """
    Load top 5000 candidates into a dictionary keyed by candidate_id.

    This lets us quickly look up domain_fit_score and talent_score.
    """
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"Top 5000 file not found: {csv_path}")

    lookup = {}

    with open(csv_path, "r", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            candidate_id = row.get("candidate_id", "").strip()
            if not candidate_id:
                continue

            lookup[candidate_id] = {
                "current_title": row.get("current_title", "").strip(),
                "domain_fit_score": _safe_float(row.get("domain_fit_score")),
                "talent_score": _safe_float(row.get("talent_score")),
            }

    return lookup


def load_semantic_matches(csv_path: str) -> list:
    """Load semantic search results from CSV."""
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"Semantic matches file not found: {csv_path}")

    matches = []

    with open(csv_path, "r", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            candidate_id = row.get("candidate_id", "").strip()
            if not candidate_id:
                continue

            matches.append(
                {
                    "candidate_id": candidate_id,
                    "similarity_score": _safe_float(row.get("similarity_score")),
                    "current_title": row.get("current_title", "").strip(),
                }
            )

    return matches


def calculate_final_score(
    similarity_score: float,
    domain_fit_score: float,
    talent_score: float,
) -> float:
    """
    Calculate the hybrid final score.

    Formula:
        final_score =
            (0.50 * similarity_score * 100)
            + (0.30 * domain_fit_score)
            + (0.20 * talent_score)

    similarity_score is usually between 0 and 1, so we multiply by 100
    to put it on a similar scale as the other 0-100 scores.
    """
    semantic_component = SIMILARITY_WEIGHT * similarity_score * 100
    domain_component = DOMAIN_FIT_WEIGHT * domain_fit_score
    talent_component = TALENT_SCORE_WEIGHT * talent_score

    final_score = semantic_component + domain_component + talent_component
    return round(final_score, 2)


def build_hybrid_ranking(semantic_matches: list, top_5000_lookup: dict) -> list:
    """
    Merge semantic matches with domain/talent scores and compute final_score.
    """
    ranked_candidates = []

    for match in semantic_matches:
        candidate_id = match["candidate_id"]
        candidate_data = top_5000_lookup.get(candidate_id, {})

        # Use title from semantic file first, then fall back to top 5000 data.
        current_title = match.get("current_title") or candidate_data.get(
            "current_title", "N/A"
        )

        similarity_score = match.get("similarity_score", 0.0)
        domain_fit_score = candidate_data.get("domain_fit_score", 0.0)
        talent_score = candidate_data.get("talent_score", 0.0)

        final_score = calculate_final_score(
            similarity_score,
            domain_fit_score,
            talent_score,
        )

        ranked_candidates.append(
            {
                "candidate_id": candidate_id,
                "current_title": current_title,
                "similarity_score": round(similarity_score, 4),
                "domain_fit_score": round(domain_fit_score, 2),
                "talent_score": round(talent_score, 2),
                "final_score": final_score,
            }
        )

    # Sort highest final_score first.
    ranked_candidates.sort(key=lambda row: row["final_score"], reverse=True)

    # Add rank numbers after sorting.
    for index, candidate in enumerate(ranked_candidates, start=1):
        candidate["rank"] = index

    return ranked_candidates


def save_hybrid_results(results: list, output_path: str) -> None:
    """Save hybrid ranking results to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fieldnames = [
        "rank",
        "candidate_id",
        "current_title",
        "similarity_score",
        "domain_fit_score",
        "talent_score",
        "final_score",
    ]

    with open(output_path, "w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


def print_leaderboard(results: list) -> None:
    """Print a compact leaderboard table."""
    print("\nHybrid Ranking Leaderboard")
    print("-" * 72)
    print(f"{'Rank':<6} {'Candidate ID':<16} {'Final Score':>12}  Title")
    print("-" * 72)

    for candidate in results:
        print(
            f"{candidate['rank']:<6} "
            f"{candidate['candidate_id']:<16} "
            f"{candidate['final_score']:>12.2f}  "
            f"{candidate['current_title']}"
        )


def print_top_candidate_details(top_candidate: dict) -> None:
    """Print detailed information for the #1 ranked candidate."""
    print("\nTop Candidate Details")
    print("-" * 21)
    print(f"  Rank              : {top_candidate['rank']}")
    print(f"  Candidate ID      : {top_candidate['candidate_id']}")
    print(f"  Title             : {top_candidate['current_title']}")
    print(f"  Final Score       : {top_candidate['final_score']:.2f}")
    print(f"  Similarity Score  : {top_candidate['similarity_score']:.4f}")
    print(f"  Domain Fit Score  : {top_candidate['domain_fit_score']:.2f}")
    print(f"  Talent Score      : {top_candidate['talent_score']:.2f}")


if __name__ == "__main__":
    print("=" * 72)
    print("Hybrid Candidate Search")
    print("=" * 72)
    print(f"Top 5000 file      : {TOP_5000_FILE}")
    print(f"Semantic matches   : {SEMANTIC_MATCHES_FILE}")
    print(f"Output file        : {OUTPUT_FILE}")
    print(
        f"Formula: final_score = "
        f"({SIMILARITY_WEIGHT} * similarity * 100) + "
        f"({DOMAIN_FIT_WEIGHT} * domain_fit) + "
        f"({TALENT_SCORE_WEIGHT} * talent)"
    )
    print()

    start_time = time.perf_counter()

    try:
        # Step 1: Load both CSV files.
        top_5000_lookup = load_top_5000_lookup(TOP_5000_FILE)
        semantic_matches = load_semantic_matches(SEMANTIC_MATCHES_FILE)

        print(f"Loaded {len(top_5000_lookup):,} candidates from top 5000 CSV.")
        print(f"Loaded {len(semantic_matches):,} semantic matches.")

        if not semantic_matches:
            raise ValueError("No semantic matches found to rank.")

        # Step 2: Merge data and calculate final_score.
        hybrid_results = build_hybrid_ranking(semantic_matches, top_5000_lookup)

        # Step 3: Save ranked output.
        save_hybrid_results(hybrid_results, OUTPUT_FILE)

        end_time = time.perf_counter()
        elapsed_seconds = end_time - start_time

        # Step 4: Print leaderboard and top candidate details.
        print_leaderboard(hybrid_results)
        print_top_candidate_details(hybrid_results[0])

        print()
        print(f"Saved results to: {OUTPUT_FILE}")
        print(f"Runtime         : {elapsed_seconds:.4f} seconds")
        print("=" * 72)

    except FileNotFoundError as error:
        print(f"ERROR: {error}")
    except ValueError as error:
        print(f"ERROR: {error}")
    except OSError as error:
        print(f"ERROR: Could not read/write files. {error}")
