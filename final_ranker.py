"""
final_ranker.py

Creates the final recruiter ranking by combining semantic similarity,
domain fit, talent score, and candidate explanations.
"""

import csv
import json
import os


PROJECT_ROOT = os.path.dirname(__file__)

SEMANTIC_RESULTS_FILE = os.path.join(PROJECT_ROOT, "outputs", "top_100_semantic_v2.csv")
TOP_5000_FILE = os.path.join(PROJECT_ROOT, "outputs", "top_5000_candidates.csv")
EXPLANATIONS_FILE = os.path.join(PROJECT_ROOT, "outputs", "top_20_explanations.json")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "outputs", "final_ranked_candidates.json")

# Weights for the final recruiter ranking formula.
SEMANTIC_WEIGHT = 0.40
DOMAIN_FIT_WEIGHT = 0.35
TALENT_WEIGHT = 0.25

# Number of candidates to keep in the final output.
FINAL_TOP_N = 20
LEADERBOARD_SIZE = 10


def _safe_float(value, default: float = 0.0) -> float:
    """Convert a value to float safely."""
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def load_semantic_results(csv_path: str) -> list:
    """Load semantic search results from CSV."""
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"Semantic results file not found: {csv_path}")

    results = []

    with open(csv_path, "r", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            candidate_id = row.get("candidate_id", "").strip()
            if not candidate_id:
                continue

            results.append(
                {
                    "candidate_id": candidate_id,
                    "current_title": row.get("current_title", "").strip(),
                    "semantic_similarity": _safe_float(row.get("similarity_score")),
                    "domain_fit_score": _safe_float(row.get("domain_fit_score")),
                    "talent_score": _safe_float(row.get("talent_score")),
                }
            )

    return results


def load_top_5000_lookup(csv_path: str) -> dict:
    """
    Load top 5000 candidate metadata as a lookup table.

    Used as a fallback when semantic results are missing fields.
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


def load_explanations(json_path: str) -> dict:
    """
    Load candidate explanations from JSON.

    Returns a dictionary keyed by candidate_id.
    """
    if not os.path.isfile(json_path):
        raise FileNotFoundError(f"Explanations file not found: {json_path}")

    with open(json_path, "r", encoding="utf-8") as json_file:
        explanation_list = json.load(json_file)

    explanations = {}
    for item in explanation_list:
        candidate_id = str(item.get("candidate_id", "")).strip()
        if candidate_id:
            explanations[candidate_id] = item.get("explanation", [])

    return explanations


def calculate_final_score(
    semantic_similarity: float,
    domain_fit_score: float,
    talent_score: float,
) -> float:
    """
    Calculate the final recruiter ranking score.

    Formula:
        final_score =
            (0.40 * semantic_similarity * 100)
            + (0.35 * domain_fit_score)
            + (0.25 * talent_score)
    """
    semantic_component = SEMANTIC_WEIGHT * semantic_similarity * 100
    domain_component = DOMAIN_FIT_WEIGHT * domain_fit_score
    talent_component = TALENT_WEIGHT * talent_score

    final_score = semantic_component + domain_component + talent_component
    return round(final_score, 2)


def build_final_ranking(
    semantic_results: list,
    top_5000_lookup: dict,
    explanations: dict,
) -> list:
    """
    Merge all inputs and compute final scores for each candidate.
    """
    ranked_candidates = []

    for row in semantic_results:
        candidate_id = row["candidate_id"]
        fallback = top_5000_lookup.get(candidate_id, {})

        current_title = row.get("current_title") or fallback.get("current_title", "N/A")
        semantic_similarity = row.get("semantic_similarity", 0.0)
        domain_fit_score = row.get("domain_fit_score") or fallback.get("domain_fit_score", 0.0)
        talent_score = row.get("talent_score") or fallback.get("talent_score", 0.0)

        final_score = calculate_final_score(
            semantic_similarity,
            domain_fit_score,
            talent_score,
        )

        # Use explanation bullets when available; otherwise provide a simple fallback.
        explanation = explanations.get(
            candidate_id,
            ["Ranked highly based on semantic and scoring signals."],
        )

        ranked_candidates.append(
            {
                "candidate_id": candidate_id,
                "current_title": current_title,
                "semantic_similarity": round(semantic_similarity, 4),
                "domain_fit_score": round(domain_fit_score, 2),
                "talent_score": round(talent_score, 2),
                "final_score": final_score,
                "explanation": explanation,
            }
        )

    # Sort by final score (highest first) and keep top 20.
    ranked_candidates.sort(key=lambda item: item["final_score"], reverse=True)
    top_candidates = ranked_candidates[:FINAL_TOP_N]

    # Add rank numbers after sorting.
    for index, candidate in enumerate(top_candidates, start=1):
        candidate["rank"] = index

    return top_candidates


def save_final_ranking(results: list, output_path: str) -> None:
    """Save final ranked candidates to JSON."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as output_file:
        json.dump(results, output_file, indent=2, ensure_ascii=False)


def print_leaderboard(results: list, top_n: int = LEADERBOARD_SIZE) -> None:
    """Print a compact top-N leaderboard."""
    print(f"\nTop {top_n} Leaderboard")
    print("-" * 72)
    print(f"{'Rank':<6} {'Candidate ID':<16} {'Final Score':>12}  Title")
    print("-" * 72)

    for candidate in results[:top_n]:
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
    print(f"  Rank               : {top_candidate['rank']}")
    print(f"  Candidate ID       : {top_candidate['candidate_id']}")
    print(f"  Title              : {top_candidate['current_title']}")
    print(f"  Final Score        : {top_candidate['final_score']:.2f}")
    print(f"  Semantic Similarity: {top_candidate['semantic_similarity']:.4f}")
    print(f"  Domain Fit Score   : {top_candidate['domain_fit_score']:.2f}")
    print(f"  Talent Score       : {top_candidate['talent_score']:.2f}")

    print("\n  Why Matched:")
    for bullet in top_candidate.get("explanation", []):
        print(f"    • {bullet}")


if __name__ == "__main__":
    print("=" * 72)
    print("Final Recruiter Ranking")
    print("=" * 72)
    print(f"Semantic results : {SEMANTIC_RESULTS_FILE}")
    print(f"Top 5000 CSV     : {TOP_5000_FILE}")
    print(f"Explanations     : {EXPLANATIONS_FILE}")
    print(f"Output JSON      : {OUTPUT_FILE}")
    print(
        f"Formula: final_score = "
        f"({SEMANTIC_WEIGHT} * semantic_similarity * 100) + "
        f"({DOMAIN_FIT_WEIGHT} * domain_fit_score) + "
        f"({TALENT_WEIGHT} * talent_score)"
    )
    print()

    try:
        # Step 1: Load all input files.
        semantic_results = load_semantic_results(SEMANTIC_RESULTS_FILE)
        top_5000_lookup = load_top_5000_lookup(TOP_5000_FILE)
        explanations = load_explanations(EXPLANATIONS_FILE)

        print(f"Loaded {len(semantic_results)} semantic search results.")
        print(f"Loaded {len(top_5000_lookup):,} candidates from top 5000 CSV.")
        print(f"Loaded {len(explanations)} candidate explanations.")

        # Step 2: Merge data, calculate final_score, and keep top 20.
        final_ranking = build_final_ranking(
            semantic_results,
            top_5000_lookup,
            explanations,
        )

        # Step 3: Save final ranked candidates.
        save_final_ranking(final_ranking, OUTPUT_FILE)

        # Step 4: Print leaderboard and top candidate details.
        print_leaderboard(final_ranking, top_n=LEADERBOARD_SIZE)
        print_top_candidate_details(final_ranking[0])

        print()
        print(f"Saved final ranking to: {OUTPUT_FILE}")
        print("=" * 72)

    except FileNotFoundError as error:
        print(f"ERROR: {error}")
    except (ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}")
    except OSError as error:
        print(f"ERROR: Could not read/write files. {error}")
