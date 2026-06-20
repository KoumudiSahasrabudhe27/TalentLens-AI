"""
dataset_analysis.py

Analyzes all candidates in candidates.jsonl without loading the full file into memory.
We read one line at a time, which is the standard approach for large datasets.
"""

import json
import os
import statistics
from collections import Counter


# Path to the raw candidate file (relative to this script).
DATA_FILE = os.path.join(
    os.path.dirname(__file__),
    "data",
    "raw",
    "candidates.jsonl",
)

# Where to save the final analysis report.
OUTPUT_FILE = os.path.join(
    os.path.dirname(__file__),
    "outputs",
    "dataset_analysis.txt",
)

# Print a progress message after this many candidates are processed.
PROGRESS_INTERVAL = 10_000


def _safe_float(value, default=None):
    """Convert a value to float when possible."""
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _experience_bucket(years: float) -> str:
    """
    Place each candidate into one experience range bucket.

    Buckets:
      0-2 years, 2-5 years, 5-10 years, 10+ years
    """
    if years < 2:
        return "0-2 years"
    if years < 5:
        return "2-5 years"
    if years < 10:
        return "5-10 years"
    return "10+ years"


def analyze_dataset(file_path: str) -> dict:
    """
    Stream through candidates.jsonl and compute dataset-wide statistics.

    Returns a dictionary with all calculated metrics.
    """
    # Counters for top skills and job titles.
    skill_counter = Counter()
    title_counter = Counter()

    # Counters for experience buckets.
    experience_bucket_counter = Counter(
        {
            "0-2 years": 0,
            "2-5 years": 0,
            "5-10 years": 0,
            "10+ years": 0,
        }
    )

    # Lists used by statistics.mean / min / max for years of experience.
    years_list = []

    # Running totals for averages (we could also use lists + statistics.mean).
    recruiter_response_rates = []
    interview_completion_rates = []
    notice_period_days_list = []

    # Count how many candidates are open to work.
    open_to_work_count = 0
    total_candidates = 0

    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Dataset file not found: {file_path}")

    # Open file once and process line by line (memory efficient).
    with open(file_path, "r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            # Skip empty lines safely.
            line = line.strip()
            if not line:
                continue

            # Parse one JSON object from the current line.
            try:
                candidate = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON on line {line_number}: {error}"
                ) from error

            total_candidates += 1

            # --- Profile fields ---
            profile = candidate.get("profile", {})
            if not isinstance(profile, dict):
                profile = {}

            years = _safe_float(profile.get("years_of_experience"))
            if years is not None:
                years_list.append(years)
                experience_bucket_counter[_experience_bucket(years)] += 1

            current_title = profile.get("current_title")
            if current_title:
                title_counter[str(current_title)] += 1

            # --- Redrob signals ---
            redrob_signals = candidate.get("redrob_signals", {})
            if not isinstance(redrob_signals, dict):
                redrob_signals = {}

            if redrob_signals.get("open_to_work_flag") is True:
                open_to_work_count += 1

            response_rate = _safe_float(redrob_signals.get("recruiter_response_rate"))
            if response_rate is not None:
                recruiter_response_rates.append(response_rate)

            interview_rate = _safe_float(redrob_signals.get("interview_completion_rate"))
            if interview_rate is not None:
                interview_completion_rates.append(interview_rate)

            notice_days = _safe_float(redrob_signals.get("notice_period_days"))
            if notice_days is not None:
                notice_period_days_list.append(notice_days)

            # --- Skills ---
            skills = candidate.get("skills", [])
            if isinstance(skills, list):
                for skill in skills:
                    if isinstance(skill, dict) and skill.get("name"):
                        skill_counter[str(skill["name"])] += 1

            # Print progress every 10,000 candidates.
            if total_candidates % PROGRESS_INTERVAL == 0:
                print(f"Processed {total_candidates:,} candidates...")

    # Build final metrics after the full pass is complete.
    open_to_work_percentage = 0.0
    if total_candidates > 0:
        open_to_work_percentage = (open_to_work_count / total_candidates) * 100

    results = {
        "total_candidates": total_candidates,
        "average_years_of_experience": statistics.mean(years_list) if years_list else 0.0,
        "min_years_of_experience": min(years_list) if years_list else 0.0,
        "max_years_of_experience": max(years_list) if years_list else 0.0,
        "open_to_work_percentage": open_to_work_percentage,
        "average_recruiter_response_rate": (
            statistics.mean(recruiter_response_rates) if recruiter_response_rates else 0.0
        ),
        "average_interview_completion_rate": (
            statistics.mean(interview_completion_rates) if interview_completion_rates else 0.0
        ),
        "average_notice_period_days": (
            statistics.mean(notice_period_days_list) if notice_period_days_list else 0.0
        ),
        "top_20_skills": skill_counter.most_common(20),
        "top_20_job_titles": title_counter.most_common(20),
        "experience_buckets": dict(experience_bucket_counter),
    }

    return results


def format_report(results: dict) -> str:
    """Convert analysis results into a readable text report."""
    lines = []
    lines.append("=" * 60)
    lines.append("TalentLens-AI Dataset Analysis")
    lines.append("=" * 60)
    lines.append("")

    lines.append("Overview")
    lines.append("-" * 8)
    lines.append(f"Total candidates: {results['total_candidates']:,}")
    lines.append("")

    lines.append("Years of Experience")
    lines.append("-" * 19)
    lines.append(f"Average: {results['average_years_of_experience']:.2f}")
    lines.append(f"Min:     {results['min_years_of_experience']:.2f}")
    lines.append(f"Max:     {results['max_years_of_experience']:.2f}")
    lines.append("")

    lines.append("Redrob Signals")
    lines.append("-" * 14)
    lines.append(f"Open to work: {results['open_to_work_percentage']:.2f}%")
    lines.append(
        f"Average recruiter response rate: {results['average_recruiter_response_rate']:.4f}"
    )
    lines.append(
        f"Average interview completion rate: {results['average_interview_completion_rate']:.4f}"
    )
    lines.append(
        f"Average notice period (days): {results['average_notice_period_days']:.2f}"
    )
    lines.append("")

    lines.append("Experience Buckets")
    lines.append("-" * 18)
    for bucket_name in ["0-2 years", "2-5 years", "5-10 years", "10+ years"]:
        count = results["experience_buckets"].get(bucket_name, 0)
        percentage = 0.0
        if results["total_candidates"] > 0:
            percentage = (count / results["total_candidates"]) * 100
        lines.append(f"  {bucket_name:<12}: {count:>7,} ({percentage:>5.2f}%)")
    lines.append("")

    lines.append("Top 20 Most Common Skills")
    lines.append("-" * 25)
    for index, (skill_name, count) in enumerate(results["top_20_skills"], start=1):
        lines.append(f"  {index:>2}. {skill_name:<35} {count:>7,}")
    lines.append("")

    lines.append("Top 20 Current Job Titles")
    lines.append("-" * 25)
    for index, (title, count) in enumerate(results["top_20_job_titles"], start=1):
        lines.append(f"  {index:>2}. {title:<35} {count:>7,}")

    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


if __name__ == "__main__":
    print("=" * 60)
    print("Starting dataset analysis...")
    print("=" * 60)

    try:
        results = analyze_dataset(DATA_FILE)
        report = format_report(results)

        # Print report to terminal.
        print("\n" + report)

        # Save report to outputs/dataset_analysis.txt
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as output:
            output.write(report)

        print(f"\nSaved analysis to: {OUTPUT_FILE}")

    except FileNotFoundError as error:
        print(f"ERROR: {error}")
    except ValueError as error:
        print(f"ERROR: {error}")
    except OSError as error:
        print(f"ERROR: Could not read/write files. {error}")
