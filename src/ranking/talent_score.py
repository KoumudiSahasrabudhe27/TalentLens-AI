"""
talent_score.py

Combines experience, hireability, and availability into one Talent Score.
This is the first overall Talent Intelligence Score for candidate ranking.
"""

import json
import os
import sys


# Add src/ to the import path so we can use other project modules.
_src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

from features.feature_extractor import extract_features
from ranking.availability_score import calculate_availability
from ranking.hireability_score import calculate_hireability


# Experience can contribute up to 20 points to the final Talent Score.
MAX_EXPERIENCE_POINTS = 20

# Candidates with 10+ years receive the full experience score.
FULL_EXPERIENCE_YEARS = 10

# Hireability and availability each contribute up to 40 points.
# Both source scores are on a 0-100 scale, so we multiply by 0.40.
HIREABILITY_WEIGHT = 0.40
AVAILABILITY_WEIGHT = 0.40


def _clamp(value: float, minimum: float, maximum: float) -> float:
    """Keep a number inside a safe range."""
    return max(minimum, min(value, maximum))


def _calculate_experience_score(years_of_experience: float) -> float:
    """
    Convert years of experience into a score from 0 to 20.

    Rules:
      - 0 years  -> 0 points
      - 10+ years -> 20 points (full score)
      - Values in between scale linearly.
    """
    if years_of_experience <= 0:
        return 0.0

    # Example: 5 years -> (5 / 10) * 20 = 10 points.
    experience_ratio = min(years_of_experience / FULL_EXPERIENCE_YEARS, 1.0)
    return experience_ratio * MAX_EXPERIENCE_POINTS


def _score_label(score_0_to_100: float) -> str:
    """
    Turn a 0-100 score into a simple recruiter-friendly label.

    Used for interpretations like "Strong availability but moderate hireability."
    """
    if score_0_to_100 >= 70:
        return "Strong"
    if score_0_to_100 >= 40:
        return "Moderate"
    return "Limited"


def generate_recruiter_interpretation(
    hireability_raw: float, availability_raw: float
) -> str:
    """
    Build a short recruiter-style sentence from hireability and availability.

    Example: "Strong availability but moderate hireability."
    """
    hireability_label = _score_label(hireability_raw)
    availability_label = _score_label(availability_raw)

    hireability_text = hireability_label.lower()
    availability_text = availability_label.lower()

    if hireability_label == availability_label:
        return f"{availability_label} availability and {hireability_text} hireability."

    return f"{availability_label} availability but {hireability_text} hireability."


def calculate_talent_score(candidate: dict) -> dict:
    """
    Calculate the overall Talent Intelligence Score for one candidate.

    Formula:
        Talent Score =
            Experience Score
            + (Hireability Score * 0.40)
            + (Availability Score * 0.40)

    Args:
        candidate: A single candidate object from candidates.jsonl.

    Returns:
        Dictionary with talent_score and each component contribution.
    """
    if not isinstance(candidate, dict):
        candidate = {}

    # Step 1: Extract flat features (includes years_of_experience).
    features = extract_features(candidate)

    # Step 2: Calculate experience component (0 to 20 points).
    years_of_experience = float(features.get("years_of_experience", 0.0) or 0.0)
    experience_score = _calculate_experience_score(years_of_experience)

    # Step 3: Calculate hireability on a 0-100 scale, then weight to 0-40.
    hireability_result = calculate_hireability(features)
    hireability_raw = float(hireability_result.get("final_score", 0.0) or 0.0)
    hireability_component = hireability_raw * HIREABILITY_WEIGHT

    # Step 4: Calculate availability on a 0-100 scale, then weight to 0-40.
    availability_result = calculate_availability(candidate)
    availability_raw = float(availability_result.get("final_score", 0.0) or 0.0)
    availability_component = availability_raw * AVAILABILITY_WEIGHT

    # Step 5: Add all three parts together for the final Talent Score.
    talent_score = experience_score + hireability_component + availability_component
    talent_score = round(_clamp(talent_score, 0.0, 100.0), 2)

    return {
        "talent_score": talent_score,
        "experience_score": round(experience_score, 2),
        "hireability_score": round(hireability_component, 2),
        "availability_score": round(availability_component, 2),
    }


def _print_talent_score_report(candidate_id: str, result: dict) -> None:
    """Print a clean score breakdown for the test block."""
    # Convert weighted components back to 0-100 scale for interpretation labels.
    hireability_raw = result["hireability_score"] / HIREABILITY_WEIGHT
    availability_raw = result["availability_score"] / AVAILABILITY_WEIGHT

    interpretation = generate_recruiter_interpretation(hireability_raw, availability_raw)

    print("=" * 60)
    print("Talent Intelligence Score - Test Run")
    print("=" * 60)
    print(f"\nCandidate ID: {candidate_id}\n")

    print("Score Breakdown")
    print("-" * 15)
    print(f"  Experience component     : {result['experience_score']:>6.2f} / {MAX_EXPERIENCE_POINTS}")
    print(
        f"  Hireability component    : {result['hireability_score']:>6.2f} / 40"
        f"  (raw: {hireability_raw:.2f})"
    )
    print(
        f"  Availability component   : {result['availability_score']:>6.2f} / 40"
        f"  (raw: {availability_raw:.2f})"
    )

    print("\nFinal Talent Score")
    print("-" * 18)
    print(f"  {result['talent_score']:.2f} / 100")

    print("\nRecruiter Interpretation")
    print("-" * 24)
    print(f"  {interpretation}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    data_file = os.path.join(project_root, "data", "raw", "candidates.jsonl")

    try:
        with open(data_file, "r", encoding="utf-8") as file:
            first_line = file.readline()

        if not first_line.strip():
            raise ValueError(f"No data found in {data_file}")

        candidate = json.loads(first_line)
        candidate_id = candidate.get("candidate_id", "N/A")
        result = calculate_talent_score(candidate)
        _print_talent_score_report(candidate_id, result)

    except FileNotFoundError:
        print(f"ERROR: Could not find dataset file at {data_file}")
    except json.JSONDecodeError as error:
        print(f"ERROR: Invalid JSON on the first line of {data_file}")
        print(error)
    except (ValueError, OSError) as error:
        print(f"ERROR: {error}")
