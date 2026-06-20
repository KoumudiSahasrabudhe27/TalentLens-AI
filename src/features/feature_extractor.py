"""
feature_extractor.py

Turns one raw candidate JSON record into a small, flat feature dictionary.
Feature extraction is a common data-engineering step before ranking or ML models.
"""

import json
import os


def _safe_list(value) -> list:
    """Return value when it is a list; otherwise return an empty list."""
    return value if isinstance(value, list) else []


def _safe_dict(value) -> dict:
    """Return value when it is a dict; otherwise return an empty dict."""
    return value if isinstance(value, dict) else {}


def _safe_float(value, default: float = 0.0) -> float:
    """Convert a value to float when possible; otherwise use default."""
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value, default: int = 0) -> int:
    """Convert a value to int when possible; otherwise use default."""
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_bool(value, default: bool = False) -> bool:
    """Return a boolean when the value is already bool; otherwise use default."""
    if isinstance(value, bool):
        return value
    return default


def extract_features(candidate: dict) -> dict:
    """
    Convert one candidate record into a simplified feature dictionary.

    Args:
        candidate: A single candidate object from candidates.jsonl.

    Returns:
        A flat dictionary of numeric and boolean features for ranking/analysis.
    """
    # Guard against missing or invalid input at the top level.
    if not isinstance(candidate, dict):
        candidate = {}

    # Pull nested sections we will read from repeatedly.
    profile = _safe_dict(candidate.get("profile"))
    skills = _safe_list(candidate.get("skills"))
    career_history = _safe_list(candidate.get("career_history"))
    education = _safe_list(candidate.get("education"))
    redrob_signals = _safe_dict(candidate.get("redrob_signals"))

    # candidate_id: unique identifier used to join features back to a person.
    candidate_id = str(candidate.get("candidate_id", ""))

    # years_of_experience: total professional experience from the profile block.
    years_of_experience = _safe_float(profile.get("years_of_experience"), default=0.0)

    # skill_count: how many skills the candidate listed on their profile.
    skill_count = len(skills)

    # career_history_count: number of past/current job entries.
    career_history_count = len(career_history)

    # education_count: number of degree or school records.
    education_count = len(education)

    # avg_skill_endorsements: average endorsements across all listed skills.
    # Endorsements suggest how strongly peers validate each skill.
    endorsement_values = []
    for skill in skills:
        if isinstance(skill, dict):
            endorsement_values.append(_safe_int(skill.get("endorsements"), default=0))

    if endorsement_values:
        avg_skill_endorsements = sum(endorsement_values) / len(endorsement_values)
    else:
        avg_skill_endorsements = 0.0

    # github_activity_score: platform signal for open-source activity (0-100, or -1 if none).
    github_activity_score = _safe_float(
        redrob_signals.get("github_activity_score"), default=0.0
    )

    # recruiter_response_rate: fraction of recruiter messages the candidate replies to.
    recruiter_response_rate = _safe_float(
        redrob_signals.get("recruiter_response_rate"), default=0.0
    )

    # interview_completion_rate: fraction of scheduled interviews actually attended.
    interview_completion_rate = _safe_float(
        redrob_signals.get("interview_completion_rate"), default=0.0
    )

    # open_to_work: whether the candidate marked themselves as open to new roles.
    open_to_work = _safe_bool(redrob_signals.get("open_to_work_flag"), default=False)

    # notice_period_days: how many days before the candidate can join a new job.
    notice_period_days = _safe_int(redrob_signals.get("notice_period_days"), default=0)

    return {
        "candidate_id": candidate_id,
        "years_of_experience": years_of_experience,
        "skill_count": skill_count,
        "career_history_count": career_history_count,
        "education_count": education_count,
        "avg_skill_endorsements": avg_skill_endorsements,
        "github_activity_score": github_activity_score,
        "recruiter_response_rate": recruiter_response_rate,
        "interview_completion_rate": interview_completion_rate,
        "open_to_work": open_to_work,
        "notice_period_days": notice_period_days,
    }


if __name__ == "__main__":
    # Build a path to the first candidate file relative to the project root.
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    data_file = os.path.join(project_root, "data", "raw", "candidates.jsonl")

    print("=" * 60)
    print("Feature Extractor - Test Run")
    print("=" * 60)

    try:
        with open(data_file, "r", encoding="utf-8") as file:
            first_line = file.readline()

        if not first_line.strip():
            raise ValueError(f"No data found in {data_file}")

        candidate = json.loads(first_line)
        features = extract_features(candidate)

        print("\nExtracted features from the first candidate:\n")
        for key, value in features.items():
            print(f"  {key:<28}: {value}")

        print("\n" + "=" * 60)

    except FileNotFoundError:
        print(f"ERROR: Could not find dataset file at {data_file}")
    except json.JSONDecodeError as error:
        print(f"ERROR: Invalid JSON on the first line of {data_file}")
        print(error)
    except (ValueError, OSError) as error:
        print(f"ERROR: {error}")
