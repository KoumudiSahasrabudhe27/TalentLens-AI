"""
domain_fit_score.py

Measures how closely a candidate's background aligns with the Senior AI Engineer JD.
Uses titles, career history, skill names, and keyword matching.
"""

import json
import os
from typing import List, Tuple


# Terms that strongly signal relevance to search, ranking, and AI systems.
HIGH_VALUE_TERMS = [
    "retrieval",
    "ranking",
    "search",
    "recommendation",
    "matching",
    "relevance",
    "embeddings",
    "vector database",
    "faiss",
    "milvus",
    "pinecone",
    "weaviate",
    "qdrant",
    "elasticsearch",
    "opensearch",
]

# Terms that suggest general ML / engineering relevance.
MEDIUM_VALUE_TERMS = [
    "machine learning",
    "ml",
    "nlp",
    "llm",
    "transformers",
    "fine-tuning",
    "python",
]

# Job titles that usually align well with the Senior AI Engineer role.
TITLE_BOOSTS = [
    "ML Engineer",
    "Data Engineer",
    "Backend Engineer",
    "Software Engineer",
    "Search Engineer",
    "Recommendation Engineer",
    "Cloud Engineer",
    "Full Stack Developer",
]

# Job titles that are usually less aligned with this technical role.
TITLE_PENALTIES = [
    "Marketing Manager",
    "HR Manager",
    "Sales Executive",
    "Accountant",
    "Customer Support",
]

# Points added to skill_score for each matched keyword group.
HIGH_VALUE_POINTS = 12
MEDIUM_VALUE_POINTS = 6

# How much title vs keyword matching contributes to the final score.
TITLE_WEIGHT = 0.40
SKILL_WEIGHT = 0.60


def _safe_dict(value) -> dict:
    """Return value when it is a dict; otherwise return an empty dict."""
    return value if isinstance(value, dict) else {}


def _safe_list(value) -> list:
    """Return value when it is a list; otherwise return an empty list."""
    return value if isinstance(value, list) else []


def _clamp(value: float, minimum: float, maximum: float) -> float:
    """Keep a number inside a safe range (0 to 100 for scores)."""
    return max(minimum, min(value, maximum))


def _title_matches_reference(title: str, reference_titles: list) -> bool:
    """
    Check whether a job title matches any title in a reference list.

    We use case-insensitive substring matching so
    "Senior Backend Engineer" still matches "Backend Engineer".
    """
    title_lower = title.lower().strip()
    if not title_lower:
        return False

    for reference in reference_titles:
        reference_lower = reference.lower().strip()
        if reference_lower in title_lower or title_lower in reference_lower:
            return True

    return False


def _collect_candidate_text(candidate: dict) -> Tuple[str, List[str]]:
    """
    Gather all text fields we want to search for domain keywords.

    Returns:
        - One combined lowercase text blob for keyword search
        - A list of all job titles (current + career history)
    """
    profile = _safe_dict(candidate.get("profile"))
    career_history = _safe_list(candidate.get("career_history"))
    skills = _safe_list(candidate.get("skills"))

    text_parts = []
    all_titles = []

    # 1. Current title from profile.
    current_title = str(profile.get("current_title", "")).strip()
    if current_title:
        text_parts.append(current_title)
        all_titles.append(current_title)

    # 2. Career history titles and descriptions.
    for role in career_history:
        if not isinstance(role, dict):
            continue

        role_title = str(role.get("title", "")).strip()
        role_description = str(role.get("description", "")).strip()

        if role_title:
            text_parts.append(role_title)
            all_titles.append(role_title)
        if role_description:
            text_parts.append(role_description)

    # 3. Skill names.
    for skill in skills:
        if isinstance(skill, dict) and skill.get("name"):
            text_parts.append(str(skill["name"]))

    # Join everything into one searchable string (lowercase for matching).
    combined_text = " ".join(text_parts).lower()
    return combined_text, all_titles


def _find_matched_terms(search_text: str) -> list:
    """
    Find which JD-related keywords appear in the candidate text.

    Returns a list of matched terms (high-value terms listed first).
    """
    matched_terms = []

    for term in HIGH_VALUE_TERMS:
        if term.lower() in search_text:
            matched_terms.append(term)

    for term in MEDIUM_VALUE_TERMS:
        if term.lower() in search_text:
            matched_terms.append(term)

    return matched_terms


def _calculate_skill_score(matched_terms: list) -> float:
    """
    Score keyword alignment from 0 to 100.

    High-value terms are worth more points than medium-value terms.
    """
    score = 0.0

    for term in matched_terms:
        if term in HIGH_VALUE_TERMS:
            score += HIGH_VALUE_POINTS
        elif term in MEDIUM_VALUE_TERMS:
            score += MEDIUM_VALUE_POINTS

    return round(_clamp(score, 0.0, 100.0), 2)


def _calculate_title_score(all_titles: list, current_title: str) -> float:
    """
    Score how well the candidate's titles align with the Senior AI Engineer JD.

    Boost titles increase the score; penalty titles decrease it.
    Current title is weighted more heavily than past roles.
    """
    if not all_titles:
        return 50.0

    current_title = current_title.strip()
    has_boost_current = _title_matches_reference(current_title, TITLE_BOOSTS)
    has_penalty_current = _title_matches_reference(current_title, TITLE_PENALTIES)

    has_boost_any = any(_title_matches_reference(title, TITLE_BOOSTS) for title in all_titles)
    has_penalty_any = any(
        _title_matches_reference(title, TITLE_PENALTIES) for title in all_titles
    )

    # Current title is the strongest signal for domain fit.
    if has_boost_current and not has_penalty_current:
        return 95.0
    if has_penalty_current and not has_boost_current:
        return 15.0
    if has_boost_current and has_penalty_current:
        # Rare conflict: give a middle score.
        return 55.0

    # Fall back to career history if current title is neutral.
    if has_boost_any and not has_penalty_any:
        return 80.0
    if has_penalty_any and not has_boost_any:
        return 25.0
    if has_boost_any and has_penalty_any:
        return 50.0

    # No strong boost or penalty found.
    return 50.0


def calculate_domain_fit(candidate: dict) -> dict:
    """
    Calculate how closely a candidate aligns with the Senior AI Engineer JD.

    Args:
        candidate: A single candidate object from candidates.jsonl.

    Returns:
        Dictionary with domain_fit_score, matched_terms, title_score, skill_score.
    """
    if not isinstance(candidate, dict):
        candidate = {}

    profile = _safe_dict(candidate.get("profile"))
    current_title = str(profile.get("current_title", "")).strip()

    # Step 1: Collect searchable text and titles from the candidate record.
    search_text, all_titles = _collect_candidate_text(candidate)

    # Step 2: Find JD-related keywords in skills, titles, and descriptions.
    matched_terms = _find_matched_terms(search_text)

    # Step 3: Score keyword alignment (skills + descriptions + titles).
    skill_score = _calculate_skill_score(matched_terms)

    # Step 4: Score title alignment (boosts and penalties).
    title_score = _calculate_title_score(all_titles, current_title)

    # Step 5: Combine both scores into one final domain fit score (0-100).
    domain_fit_score = (title_score * TITLE_WEIGHT) + (skill_score * SKILL_WEIGHT)
    domain_fit_score = round(_clamp(domain_fit_score, 0.0, 100.0), 2)

    return {
        "domain_fit_score": domain_fit_score,
        "matched_terms": matched_terms,
        "title_score": title_score,
        "skill_score": skill_score,
    }


def _print_domain_fit_report(candidate_id: str, candidate: dict, result: dict) -> None:
    """Print a detailed breakdown for the test block."""
    profile = _safe_dict(candidate.get("profile"))
    search_text, all_titles = _collect_candidate_text(candidate)

    print("=" * 60)
    print("Domain Fit Score - Test Run")
    print("=" * 60)
    print(f"\nCandidate ID: {candidate_id}")
    print(f"Current Title: {profile.get('current_title', 'N/A')}\n")

    print("Titles Considered")
    print("-" * 17)
    for index, title in enumerate(all_titles, start=1):
        boost = " [BOOST]" if _title_matches_reference(title, TITLE_BOOSTS) else ""
        penalty = " [PENALTY]" if _title_matches_reference(title, TITLE_PENALTIES) else ""
        print(f"  {index}. {title}{boost}{penalty}")

    print("\nMatched JD Keywords")
    print("-" * 19)
    if result["matched_terms"]:
        for index, term in enumerate(result["matched_terms"], start=1):
            value_label = "HIGH" if term in HIGH_VALUE_TERMS else "MEDIUM"
            print(f"  {index}. {term} ({value_label})")
    else:
        print("  No JD keywords matched.")

    print("\nScore Breakdown")
    print("-" * 15)
    print(f"  Title score        : {result['title_score']:.2f} / 100  (weight: {TITLE_WEIGHT:.0%})")
    print(f"  Skill/keyword score: {result['skill_score']:.2f} / 100  (weight: {SKILL_WEIGHT:.0%})")

    print("\nFinal Domain Fit Score")
    print("-" * 22)
    print(f"  {result['domain_fit_score']:.2f} / 100")

    print("\nSearch Text Preview (first 200 chars)")
    print("-" * 35)
    preview = search_text[:200] + ("..." if len(search_text) > 200 else "")
    print(f"  {preview}")

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
        result = calculate_domain_fit(candidate)
        _print_domain_fit_report(candidate_id, candidate, result)

    except FileNotFoundError:
        print(f"ERROR: Could not find dataset file at {data_file}")
    except json.JSONDecodeError as error:
        print(f"ERROR: Invalid JSON on the first line of {data_file}")
        print(error)
    except (ValueError, OSError) as error:
        print(f"ERROR: {error}")
