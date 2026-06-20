"""
availability_score.py

Calculates an Availability Score (0-100) from a candidate's redrob_signals.
Availability measures how ready and active a candidate is right now.
"""

import json
import os
from datetime import date, datetime
from typing import Optional


# Maximum points for each scoring category (total = 100).
MAX_OPEN_TO_WORK_POINTS = 40
MAX_APPLICATIONS_POINTS = 20
MAX_LAST_ACTIVE_POINTS = 30
MAX_NOTICE_PERIOD_POINTS = 10

# Notice period in the dataset can be up to 180 days.
MAX_NOTICE_PERIOD_DAYS = 180

# If a candidate applied this many times in 30 days, they get full application points.
# This is a simple benchmark for "very active" job searching.
MAX_APPLICATIONS_FOR_FULL_SCORE = 10

# If a candidate has not logged in for this many days, they get 0 last-active points.
MAX_INACTIVE_DAYS = 90


def _clamp(value: float, minimum: float, maximum: float) -> float:
    """Keep a number inside a safe range."""
    return max(minimum, min(value, maximum))


def _safe_dict(value) -> dict:
    """Return value when it is a dict; otherwise return an empty dict."""
    return value if isinstance(value, dict) else {}


def _parse_date(date_string: str) -> Optional[date]:
    """
    Convert a date string like '2026-05-20' into a Python date object.

    Returns None when the value is missing or invalid.
    """
    if not date_string or not isinstance(date_string, str):
        return None

    try:
        # datetime.strptime reads a string using a format pattern.
        # %Y = 4-digit year, %m = month, %d = day.
        return datetime.strptime(date_string.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def _days_since_last_active(last_active_date_string: str, today: Optional[date] = None) -> Optional[int]:
    """
    Calculate how many days have passed since the candidate was last active.

    Uses today's real-world date unless a custom 'today' is provided for testing.
    """
    last_active = _parse_date(last_active_date_string)
    if last_active is None:
        return None

    # date.today() gives the current local date on the machine running this code.
    reference_date = today or date.today()

    # Subtracting two date objects returns the number of days between them.
    days_since = (reference_date - last_active).days

    # Negative values can happen if data has a future date; treat as 0 days ago.
    return max(0, days_since)


def calculate_availability(candidate: dict) -> dict:
    """
    Calculate an Availability Score from one full candidate record.

    Args:
        candidate: A candidate object from candidates.jsonl.

    Returns:
        A dictionary with:
          - final_score: total score between 0 and 100
          - score_breakdown: points earned in each category
    """
    if not isinstance(candidate, dict):
        candidate = {}

    # All availability signals live inside redrob_signals.
    redrob_signals = _safe_dict(candidate.get("redrob_signals"))

    # --- 1. Open To Work (max 40 points) ---
    # True means the candidate marked themselves as open to new opportunities.
    # This is the strongest single signal that they are available now.
    open_to_work_flag = bool(redrob_signals.get("open_to_work_flag", False))
    open_to_work_points = MAX_OPEN_TO_WORK_POINTS if open_to_work_flag else 0.0

    # --- 2. Applications Submitted in Last 30 Days (max 20 points) ---
    # More applications usually means the candidate is actively applying to jobs.
    # We scale linearly up to MAX_APPLICATIONS_FOR_FULL_SCORE applications.
    # Example: 5 applications out of 10 benchmark -> (5/10) * 20 = 10 points.
    applications_submitted = int(redrob_signals.get("applications_submitted_30d", 0) or 0)
    applications_submitted = max(0, applications_submitted)

    if applications_submitted >= MAX_APPLICATIONS_FOR_FULL_SCORE:
        applications_points = float(MAX_APPLICATIONS_POINTS)
    else:
        application_ratio = applications_submitted / MAX_APPLICATIONS_FOR_FULL_SCORE
        applications_points = application_ratio * MAX_APPLICATIONS_POINTS

    # --- 3. Last Active Date (max 30 points) ---
    # More recent platform activity suggests the candidate is easier to reach.
    # We convert last_active_date into "days since last active" using today's date.
    # 0 days ago  -> 30 points (active today)
    # 90+ days ago -> 0 points (inactive for ~3 months)
    last_active_date = redrob_signals.get("last_active_date", "")
    days_since_active = _days_since_last_active(last_active_date)

    if days_since_active is None:
        # Missing or invalid date means we cannot reward recent activity.
        last_active_points = 0.0
    elif days_since_active >= MAX_INACTIVE_DAYS:
        last_active_points = 0.0
    else:
        activity_ratio = 1.0 - (days_since_active / MAX_INACTIVE_DAYS)
        last_active_points = activity_ratio * MAX_LAST_ACTIVE_POINTS

    # --- 4. Notice Period (max 10 points) ---
    # Shorter notice period means the candidate can join sooner.
    # 0 days notice  -> 10 points
    # 180 days notice -> 0 points
    notice_period_days = int(redrob_signals.get("notice_period_days", 0) or 0)
    notice_period_days = max(0, notice_period_days)

    if notice_period_days >= MAX_NOTICE_PERIOD_DAYS:
        notice_period_points = 0.0
    else:
        notice_ratio = 1.0 - (notice_period_days / MAX_NOTICE_PERIOD_DAYS)
        notice_period_points = notice_ratio * MAX_NOTICE_PERIOD_POINTS

    score_breakdown = {
        "open_to_work": round(open_to_work_points, 2),
        "applications_submitted_30d": round(applications_points, 2),
        "last_active_date": round(last_active_points, 2),
        "notice_period": round(notice_period_points, 2),
    }

    final_score = sum(score_breakdown.values())
    final_score = round(_clamp(final_score, 0.0, 100.0), 2)

    return {
        "final_score": final_score,
        "score_breakdown": score_breakdown,
    }


def _print_availability_report(
    candidate_id: str, signals: dict, result: dict, days_since_active: Optional[int]
) -> None:
    """Print a readable report for the test block."""
    breakdown = result["score_breakdown"]
    category_limits = {
        "open_to_work": MAX_OPEN_TO_WORK_POINTS,
        "applications_submitted_30d": MAX_APPLICATIONS_POINTS,
        "last_active_date": MAX_LAST_ACTIVE_POINTS,
        "notice_period": MAX_NOTICE_PERIOD_POINTS,
    }

    print("=" * 60)
    print("Availability Score - Test Run")
    print("=" * 60)
    print(f"\nCandidate ID: {candidate_id}\n")

    print("Input Signals Used for Scoring")
    print("-" * 30)
    print(f"  open_to_work_flag           : {signals.get('open_to_work_flag')}")
    print(f"  applications_submitted_30d  : {signals.get('applications_submitted_30d')}")
    print(f"  last_active_date            : {signals.get('last_active_date')}")
    print(f"  notice_period_days          : {signals.get('notice_period_days')}")
    print(f"  days_since_last_active      : {days_since_active}")
    print(f"  reference_date (today)      : {date.today().isoformat()}")

    print("\nScore Breakdown")
    print("-" * 15)
    for category, points in breakdown.items():
        maximum = category_limits[category]
        print(f"  {category:<28}: {points:>6.2f} / {maximum}")

    print("\nFinal Availability Score")
    print("-" * 24)
    print(f"  {result['final_score']:.2f} / 100")
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
        signals = candidate.get("redrob_signals", {})
        days_since_active = _days_since_last_active(signals.get("last_active_date", ""))
        result = calculate_availability(candidate)
        candidate_id = candidate.get("candidate_id", "N/A")
        _print_availability_report(candidate_id, signals, result, days_since_active)

    except FileNotFoundError:
        print(f"ERROR: Could not find dataset file at {data_file}")
    except json.JSONDecodeError as error:
        print(f"ERROR: Invalid JSON on the first line of {data_file}")
        print(error)
    except (ValueError, OSError) as error:
        print(f"ERROR: {error}")
