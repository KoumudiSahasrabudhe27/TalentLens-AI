"""
improve_explanations.py

Generates recruiter-quality explanations for final ranked candidates.
Uses real profile data so explanations are specific and trustworthy.
"""

import json
import os
import time
from typing import Optional


PROJECT_ROOT = os.path.dirname(__file__)

FINAL_RANKING_FILE = os.path.join(PROJECT_ROOT, "outputs", "final_ranked_candidates.json")
CANDIDATES_FILE = os.path.join(PROJECT_ROOT, "data", "raw", "candidates.jsonl")
OUTPUT_FILE = os.path.join(
    PROJECT_ROOT, "outputs", "final_ranked_candidates_explained.json"
)

TOP_SKILL_COUNT = 5
PRINT_TOP_N = 5

# Title keywords that indicate strong alignment with the Senior AI Engineer role.
RELEVANT_TITLE_KEYWORDS = [
    "ai engineer",
    "ml engineer",
    "machine learning",
    "search engineer",
    "nlp engineer",
    "research engineer",
    "applied scientist",
    "data engineer",
    "software engineer",
    "ai specialist",
]

# Skill keywords that are especially relevant to the job description.
HIGHLIGHT_SKILL_KEYWORDS = [
    "retrieval",
    "ranking",
    "search",
    "recommendation",
    "nlp",
    "llm",
    "embedding",
    "vector",
    "faiss",
    "milvus",
    "pinecone",
    "weaviate",
    "qdrant",
    "python",
    "transformer",
    "fine-tuning",
    "machine learning",
]


def _safe_float(value, default: float = 0.0) -> float:
    """Convert a value to float safely."""
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def load_final_ranked_candidates(json_path: str) -> list:
    """Load the top 20 final ranked candidates."""
    if not os.path.isfile(json_path):
        raise FileNotFoundError(f"Final ranking file not found: {json_path}")

    with open(json_path, "r", encoding="utf-8") as json_file:
        ranked_candidates = json.load(json_file)

    if not isinstance(ranked_candidates, list):
        raise ValueError("final_ranked_candidates.json must contain a JSON list.")

    return ranked_candidates


def load_candidate_profiles(jsonl_path: str, candidate_ids: set) -> dict:
    """
    Load candidate profiles from JSONL for a specific set of IDs.

    Reads line-by-line to avoid loading all 100,000 candidates into memory.
    """
    if not os.path.isfile(jsonl_path):
        raise FileNotFoundError(f"Candidates file not found: {jsonl_path}")

    profiles = {}

    with open(jsonl_path, "r", encoding="utf-8") as jsonl_file:
        for line in jsonl_file:
            line = line.strip()
            if not line:
                continue

            candidate = json.loads(line)
            candidate_id = str(candidate.get("candidate_id", "")).strip()

            if candidate_id in candidate_ids:
                profiles[candidate_id] = candidate

            if len(profiles) == len(candidate_ids):
                break

    return profiles


def get_top_skills(candidate: dict, limit: int = TOP_SKILL_COUNT) -> list:
    """Return top skills sorted by endorsements."""
    skills = candidate.get("skills", [])
    if not isinstance(skills, list):
        return []

    skill_items = []
    for skill in skills:
        if isinstance(skill, dict) and skill.get("name"):
            endorsements = skill.get("endorsements", 0) or 0
            try:
                endorsements = int(endorsements)
            except (TypeError, ValueError):
                endorsements = 0
            skill_items.append((skill["name"], endorsements))

    skill_items.sort(key=lambda item: item[1], reverse=True)
    return [name for name, _ in skill_items[:limit]]


def _join_items(items: list) -> str:
    """Join a list into natural English (A, B, and C)."""
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def _format_skill_display_name(skill_name: str) -> str:
    """Format a skill name for readable explanation text."""
    if skill_name.isupper() and len(skill_name) <= 5:
        return skill_name
    return skill_name.title() if skill_name.islower() else skill_name


def _is_title_relevant(title: str) -> bool:
    """Check whether the candidate title aligns with the target AI role."""
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in RELEVANT_TITLE_KEYWORDS)


def _prioritize_relevant_skills(skill_names: list) -> list:
    """
    Put JD-relevant skills first, then keep the remaining top skills.

    This makes explanations more meaningful for recruiters.
    """
    relevant = []
    other = []

    for skill_name in skill_names:
        skill_lower = skill_name.lower()
        if any(keyword in skill_lower for keyword in HIGHLIGHT_SKILL_KEYWORDS):
            relevant.append(skill_name)
        else:
            other.append(skill_name)

    return relevant + other


def explain_title(title: str) -> str:
    """Create a title-based explanation bullet."""
    if _is_title_relevant(title):
        return (
            f'Current title "{title}" closely aligns with the target AI Search role.'
        )
    return f'Current title is "{title}", which was considered during ranking.'


def explain_skills(skill_names: list) -> str:
    """Create a skills-based explanation bullet using real candidate skills."""
    if not skill_names:
        return "Candidate profile includes relevant technical background."

    ordered_skills = _prioritize_relevant_skills(skill_names)
    display_skills = [_format_skill_display_name(skill) for skill in ordered_skills[:5]]
    joined_skills = _join_items(display_skills)

    return f"Strong expertise in {joined_skills}."


def explain_experience(years_of_experience: float) -> str:
    """Create an experience-based explanation bullet."""
    if years_of_experience <= 0:
        return "Experience level was evaluated as part of the ranking process."

    years_text = f"{years_of_experience:.1f}".rstrip("0").rstrip(".")
    return f"{years_text} years of relevant experience."


def explain_domain_fit(domain_fit_score: float) -> Optional[str]:
    """Mention domain fit only when the score is strong (>80)."""
    if domain_fit_score > 80:
        return f"Excellent domain fit score ({domain_fit_score:.0f}/100)."
    return None


def explain_talent(talent_score: float) -> Optional[str]:
    """Mention talent score only when it is strong (>70)."""
    if talent_score > 70:
        return (
            f"Strong talent score ({talent_score:.0f}/100), "
            "indicating high hiring potential."
        )
    return None


def explain_semantic_similarity(semantic_similarity: float) -> Optional[str]:
    """Mention semantic similarity only when it is strong (>0.65)."""
    if semantic_similarity > 0.65:
        return "High semantic similarity to the job requirements."
    return None


def generate_explanations(ranked_row: dict, candidate_profile: dict) -> list:
    """
    Build recruiter-quality explanation bullets for one candidate.

    Uses real profile fields and score thresholds from the requirements.
    """
    profile = candidate_profile.get("profile", {})
    if not isinstance(profile, dict):
        profile = {}

    title = ranked_row.get("current_title") or profile.get("current_title", "N/A")
    years_of_experience = _safe_float(profile.get("years_of_experience"))
    top_skills = get_top_skills(candidate_profile, limit=TOP_SKILL_COUNT)

    domain_fit_score = _safe_float(ranked_row.get("domain_fit_score"))
    talent_score = _safe_float(ranked_row.get("talent_score"))
    semantic_similarity = _safe_float(ranked_row.get("semantic_similarity"))

    bullets = []

    # Rule 1: Title relevance.
    bullets.append(explain_title(str(title)))

    # Rule 2: Real top skills.
    bullets.append(explain_skills(top_skills))

    # Rule 3: Years of experience.
    bullets.append(explain_experience(years_of_experience))

    # Rule 4: Domain fit (only if > 80).
    domain_bullet = explain_domain_fit(domain_fit_score)
    if domain_bullet:
        bullets.append(domain_bullet)

    # Rule 5: Talent score (only if > 70).
    talent_bullet = explain_talent(talent_score)
    if talent_bullet:
        bullets.append(talent_bullet)

    # Rule 6: Semantic similarity (only if > 0.65).
    similarity_bullet = explain_semantic_similarity(semantic_similarity)
    if similarity_bullet:
        bullets.append(similarity_bullet)

    return bullets


def build_explained_candidates(ranked_candidates: list, profiles: dict) -> list:
    """Generate improved explanations for all final ranked candidates."""
    explained_candidates = []

    for ranked_row in ranked_candidates:
        candidate_id = ranked_row["candidate_id"]
        profile = profiles.get(candidate_id, {})
        explanations = generate_explanations(ranked_row, profile)

        explained_candidates.append(
            {
                "rank": ranked_row.get("rank"),
                "candidate_id": candidate_id,
                "title": ranked_row.get("current_title", "N/A"),
                "final_score": ranked_row.get("final_score"),
                "explanations": explanations,
            }
        )

    return explained_candidates


def save_explained_candidates(explained_candidates: list, output_path: str) -> None:
    """Save explained candidates to JSON."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as output_file:
        json.dump(explained_candidates, output_file, indent=2, ensure_ascii=False)


def print_top_candidates(explained_candidates: list, top_n: int = PRINT_TOP_N) -> None:
    """Print top candidates with their explanation bullets."""
    print(f"\nTop {top_n} Candidates With Explanations")
    print("=" * 72)

    for candidate in explained_candidates[:top_n]:
        print(
            f"\n#{candidate['rank']} {candidate['candidate_id']} — "
            f"{candidate['title']} (Final Score: {candidate['final_score']})"
        )
        print("Why Matched:")
        for bullet in candidate["explanations"]:
            print(f"  ✓ {bullet}")


if __name__ == "__main__":
    print("=" * 72)
    print("Improve Candidate Explanations")
    print("=" * 72)
    print(f"Final ranking : {FINAL_RANKING_FILE}")
    print(f"Candidates    : {CANDIDATES_FILE}")
    print(f"Output        : {OUTPUT_FILE}")
    print()

    start_time = time.perf_counter()

    try:
        # Step 1: Load top 20 final ranked candidates.
        ranked_candidates = load_final_ranked_candidates(FINAL_RANKING_FILE)
        candidate_ids = {row["candidate_id"] for row in ranked_candidates}
        print(f"Loaded {len(ranked_candidates)} ranked candidates.")

        # Step 2: Load full candidate profiles for real explanation details.
        profiles = load_candidate_profiles(CANDIDATES_FILE, candidate_ids)
        print(f"Loaded {len(profiles)} candidate profiles from JSONL.")

        missing_ids = candidate_ids - set(profiles.keys())
        if missing_ids:
            print(f"Warning: {len(missing_ids)} candidate profiles were not found.")

        # Step 3: Generate improved explanations.
        explained_candidates = build_explained_candidates(ranked_candidates, profiles)

        # Step 4: Save explained output.
        save_explained_candidates(explained_candidates, OUTPUT_FILE)

        end_time = time.perf_counter()
        elapsed_seconds = end_time - start_time

        # Step 5: Print top 5 candidates with explanations.
        print_top_candidates(explained_candidates, top_n=PRINT_TOP_N)

        print()
        print(f"Saved explained rankings to: {OUTPUT_FILE}")
        print(f"Runtime: {elapsed_seconds:.2f} seconds")
        print("=" * 72)

    except FileNotFoundError as error:
        print(f"ERROR: {error}")
    except (ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}")
    except OSError as error:
        print(f"ERROR: Could not read/write files. {error}")
