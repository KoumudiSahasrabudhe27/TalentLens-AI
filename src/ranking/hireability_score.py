"""
hireability_score.py

Calculates a Hireability Score (0-100) from extracted candidate features.
Ranking systems often combine several signals into one easy-to-read number.
"""

import json
import os
import sys


# Maximum points allowed for each scoring category.
# These add up to 100 so the final score stays on a 0-100 scale.
MAX_RESPONSE_POINTS = 40
MAX_INTERVIEW_POINTS = 25
MAX_OPEN_TO_WORK_POINTS = 15
MAX_NOTICE_PERIOD_POINTS = 10
MAX_GITHUB_POINTS = 10

# Notice period in the dataset can be up to 180 days.
# We use this as the "worst case" for the notice-period score.
MAX_NOTICE_PERIOD_DAYS = 180


def _clamp(value: float, minimum: float, maximum: float) -> float:
    """Keep a number inside a safe range (used to avoid scores above 100)."""
    return max(minimum, min(value, maximum))


def calculate_hireability(features: dict) -> dict:
    """
    Calculate a Hireability Score from a feature dictionary.

    Args:
        features: Output from extract_features(), containing hiring signals.

    Returns:
        A dictionary with:
          - final_score: total score between 0 and 100
          - score_breakdown: points earned in each category
    """
    if not isinstance(features, dict):
        features = {}

    # --- 1. Recruiter Response Rate (max 40 points) ---
    # This rate is between 0.0 and 1.0 (0% to 100% response rate).
    # Higher response rate means the candidate is more reachable.
    # Example: 0.80 response rate -> 0.80 * 40 = 32 points.
    response_rate = _clamp(float(features.get("recruiter_response_rate", 0.0) or 0.0), 0.0, 1.0)
    response_points = response_rate * MAX_RESPONSE_POINTS

    # --- 2. Interview Completion Rate (max 25 points) ---
    # Also a fraction between 0.0 and 1.0.
    # Candidates who attend scheduled interviews are more reliable hires.
    # Example: 0.60 completion rate -> 0.60 * 25 = 15 points.
    interview_rate = _clamp(float(features.get("interview_completion_rate", 0.0) or 0.0), 0.0, 1.0)
    interview_points = interview_rate * MAX_INTERVIEW_POINTS

    # --- 3. Open To Work (max 15 points) ---
    # Boolean flag: True means actively looking for opportunities.
    # If open_to_work is True, award full 15 points; otherwise 0.
    open_to_work = bool(features.get("open_to_work", False))
    open_to_work_points = MAX_OPEN_TO_WORK_POINTS if open_to_work else 0.0

    # --- 4. Notice Period (max 10 points) ---
    # Shorter notice period is better for recruiters who need fast hiring.
    # 0 days notice  -> 10 points (can join immediately)
    # 180 days notice -> 0 points (long wait time)
    # We use a simple linear scale between those two extremes.
    notice_period_days = int(features.get("notice_period_days", 0) or 0)
    notice_period_days = max(0, notice_period_days)

    if notice_period_days >= MAX_NOTICE_PERIOD_DAYS:
        notice_period_points = 0.0
    else:
        notice_ratio = 1.0 - (notice_period_days / MAX_NOTICE_PERIOD_DAYS)
        notice_period_points = notice_ratio * MAX_NOTICE_PERIOD_POINTS

    # --- 5. GitHub Activity (max 10 points) ---
    # github_activity_score is usually 0-100 from the platform.
    # -1 means no GitHub profile is linked, so we award 0 points.
    # Example: score of 50 -> (50 / 100) * 10 = 5 points.
    github_score = float(features.get("github_activity_score", 0.0) or 0.0)
    if github_score < 0:
        github_points = 0.0
    else:
        github_score = _clamp(github_score, 0.0, 100.0)
        github_points = (github_score / 100.0) * MAX_GITHUB_POINTS

    # Combine all category scores into one total.
    score_breakdown = {
        "recruiter_response_rate": round(response_points, 2),
        "interview_completion_rate": round(interview_points, 2),
        "open_to_work": round(open_to_work_points, 2),
        "notice_period": round(notice_period_points, 2),
        "github_activity": round(github_points, 2),
    }

    final_score = sum(score_breakdown.values())
    final_score = round(_clamp(final_score, 0.0, 100.0), 2)

    return {
        "final_score": final_score,
        "score_breakdown": score_breakdown,
    }


def _print_hireability_report(candidate_id: str, features: dict, result: dict) -> None:
    """Print a readable report for the test block."""
    breakdown = result["score_breakdown"]
    category_limits = {
        "recruiter_response_rate": MAX_RESPONSE_POINTS,
        "interview_completion_rate": MAX_INTERVIEW_POINTS,
        "open_to_work": MAX_OPEN_TO_WORK_POINTS,
        "notice_period": MAX_NOTICE_PERIOD_POINTS,
        "github_activity": MAX_GITHUB_POINTS,
    }

    print("=" * 60)
    print("Hireability Score - Test Run")
    print("=" * 60)
    print(f"\nCandidate ID: {candidate_id}\n")

    print("Input Features Used for Scoring")
    print("-" * 32)
    print(f"  recruiter_response_rate   : {features.get('recruiter_response_rate')}")
    print(f"  interview_completion_rate : {features.get('interview_completion_rate')}")
    print(f"  open_to_work              : {features.get('open_to_work')}")
    print(f"  notice_period_days        : {features.get('notice_period_days')}")
    print(f"  github_activity_score     : {features.get('github_activity_score')}")

    print("\nScore Breakdown")
    print("-" * 15)
    for category, points in breakdown.items():
        maximum = category_limits[category]
        print(f"  {category:<28}: {points:>6.2f} / {maximum}")

    print("\nFinal Hireability Score")
    print("-" * 23)
    print(f"  {result['final_score']:.2f} / 100")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    # Add src/ to Python path so we can import feature_extractor.
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    src_path = os.path.join(project_root, "src")
    sys.path.insert(0, src_path)

    from features.feature_extractor import extract_features

    data_file = os.path.join(project_root, "data", "raw", "candidates.jsonl")

    try:
        with open(data_file, "r", encoding="utf-8") as file:
            first_line = file.readline()

        if not first_line.strip():
            raise ValueError(f"No data found in {data_file}")

        candidate = json.loads(first_line)
        features = extract_features(candidate)
        result = calculate_hireability(features)
        _print_hireability_report(features.get("candidate_id", "N/A"), features, result)

    except FileNotFoundError:
        print(f"ERROR: Could not find dataset file at {data_file}")
    except json.JSONDecodeError as error:
        print(f"ERROR: Invalid JSON on the first line of {data_file}")
        print(error)
    except (ValueError, OSError) as error:
        print(f"ERROR: {error}")
