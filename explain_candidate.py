"""
explain_candidate.py

Generates recruiter-friendly explanations for top semantic search matches.
Uses simple rule-based logic so results are easy to understand and debug.
"""

import csv
import json
import os
from typing import Optional


PROJECT_ROOT = os.path.dirname(__file__)

SEMANTIC_RESULTS_FILE = os.path.join(PROJECT_ROOT, "outputs", "top_100_semantic_v2.csv")
TOP_5000_FILE = os.path.join(PROJECT_ROOT, "outputs", "top_5000_candidates.csv")
CANDIDATES_FILE = os.path.join(PROJECT_ROOT, "data", "raw", "candidates.jsonl")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "outputs", "top_20_explanations.json")

# How many candidates to explain and display.
TOP_N = 20
PRINT_TOP_N = 5
TOP_SKILL_COUNT = 5

# Skill keywords that indicate relevance to the Senior AI Engineer role.
RELEVANT_SKILL_KEYWORDS = [
    "retrieval",
    "ranking",
    "search",
    "recommendation",
    "embedding",
    "vector",
    "faiss",
    "milvus",
    "pinecone",
    "weaviate",
    "qdrant",
    "python",
    "machine learning",
    "nlp",
    "llm",
    "transformer",
    "fine-tuning",
    "tensorflow",
    "pytorch",
]

# Title keywords that suggest a strong role match.
STRONG_TITLE_KEYWORDS = [
    "ai engineer",
    "ml engineer",
    "machine learning",
    "search engineer",
    "nlp engineer",
    "research engineer",
    "applied scientist",
    "data engineer",
    "software engineer",
]


def _safe_float(value, default: float = 0.0) -> float:
    """Convert a value to float safely."""
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def load_top_semantic_candidates(csv_path: str, top_n: int) -> list:
    """Load the top N candidates from semantic search results."""
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"Semantic results file not found: {csv_path}")

    candidates = []

    with open(csv_path, "r", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            candidate_id = row.get("candidate_id", "").strip()
            if not candidate_id:
                continue

            candidates.append(
                {
                    "candidate_id": candidate_id,
                    "title": row.get("current_title", "").strip(),
                    "similarity_score": _safe_float(row.get("similarity_score")),
                    "pre_rank_score": _safe_float(row.get("pre_rank_score")),
                    "domain_fit_score": _safe_float(row.get("domain_fit_score")),
                    "talent_score": _safe_float(row.get("talent_score")),
                }
            )

            if len(candidates) >= top_n:
                break

    return candidates


def load_top_5000_metadata(csv_path: str) -> dict:
    """Load supplementary candidate metadata from top_5000_candidates.csv."""
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"Top 5000 file not found: {csv_path}")

    metadata = {}

    with open(csv_path, "r", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            candidate_id = row.get("candidate_id", "").strip()
            if not candidate_id:
                continue

            metadata[candidate_id] = {
                "current_title": row.get("current_title", "").strip(),
                "pre_rank_score": _safe_float(row.get("pre_rank_score")),
                "domain_fit_score": _safe_float(row.get("domain_fit_score")),
                "talent_score": _safe_float(row.get("talent_score")),
            }

    return metadata


def load_candidate_profiles(jsonl_path: str, candidate_ids: set) -> dict:
    """
    Load full candidate records from JSONL for a specific set of IDs.

    Reads line-by-line so we do not load all 100,000 candidates into memory.
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

            # Stop early once we found every candidate we need.
            if len(profiles) == len(candidate_ids):
                break

    return profiles


def get_top_skills(candidate: dict, limit: int = TOP_SKILL_COUNT) -> list:
    """
    Extract the top N skills sorted by endorsements.

    Endorsements are used as a simple signal of skill strength.
    """
    skills = candidate.get("skills", [])
    if not isinstance(skills, list):
        return []

    valid_skills = []
    for skill in skills:
        if isinstance(skill, dict) and skill.get("name"):
            endorsements = skill.get("endorsements", 0) or 0
            try:
                endorsements = int(endorsements)
            except (TypeError, ValueError):
                endorsements = 0
            valid_skills.append((skill["name"], endorsements))

    valid_skills.sort(key=lambda item: item[1], reverse=True)
    return [name for name, _ in valid_skills[:limit]]


def _find_relevant_skills(skill_names: list) -> list:
    """Return skill names that match JD-relevant keywords."""
    relevant = []

    for skill_name in skill_names:
        skill_lower = skill_name.lower()
        for keyword in RELEVANT_SKILL_KEYWORDS:
            if keyword in skill_lower:
                relevant.append(skill_name)
                break

    return relevant


def _join_skill_names(skill_names: list) -> str:
    """Join skill names into readable text."""
    if not skill_names:
        return ""
    if len(skill_names) == 1:
        return skill_names[0]
    if len(skill_names) == 2:
        return f"{skill_names[0]} and {skill_names[1]}"
    return ", ".join(skill_names[:-1]) + f", and {skill_names[-1]}"


def explain_title(title: str) -> Optional[str]:
    """Generate a title-based explanation bullet."""
    title_lower = title.lower()

    if "ai engineer" in title_lower or "ai specialist" in title_lower:
        return "Strong AI engineering background"

    if "search engineer" in title_lower:
        return "Relevant search engineering title"

    if "nlp" in title_lower:
        return "Strong NLP engineering background"

    if "machine learning" in title_lower or "ml engineer" in title_lower:
        return "Relevant machine learning expertise"

    if "research engineer" in title_lower or "applied scientist" in title_lower:
        return "Research-oriented engineering background"

    for keyword in STRONG_TITLE_KEYWORDS:
        if keyword in title_lower:
            return f"Relevant title aligned with the role ({title})"

    return None


def explain_skills(skill_names: list) -> Optional[str]:
    """Generate a skills-based explanation bullet."""
    relevant_skills = _find_relevant_skills(skill_names)

    if not relevant_skills:
        if skill_names:
            return f"Top skills include {_join_skill_names(skill_names[:3])}"
        return None

    joined = _join_skill_names(relevant_skills[:3])

    if any("retrieval" in skill.lower() or "ranking" in skill.lower() for skill in relevant_skills):
        return "Experience with retrieval and ranking systems"

    if any("embedding" in skill.lower() or "vector" in skill.lower() for skill in relevant_skills):
        return "Experience with embeddings and vector search technologies"

    return f"Relevant technical skills: {joined}"


def explain_domain_fit(domain_fit_score: float) -> Optional[str]:
    """Generate a domain-fit explanation bullet."""
    if domain_fit_score >= 80:
        return "Excellent domain fit for AI search and ranking systems"
    if domain_fit_score >= 65:
        return "Good domain alignment with role requirements"
    if domain_fit_score >= 50:
        return "Moderate domain fit based on skills and career history"
    return None


def explain_talent(talent_score: float) -> Optional[str]:
    """Generate a talent-score explanation bullet."""
    if talent_score >= 75:
        return "High talent score based on engagement and availability signals"
    if talent_score >= 60:
        return "Solid talent score with positive hiring indicators"
    return None


def explain_similarity(similarity_score: float) -> Optional[str]:
    """Generate a semantic-match explanation bullet."""
    if similarity_score >= 0.70:
        return "Strong semantic match to the job search query"
    if similarity_score >= 0.65:
        return "Good semantic relevance to the role requirements"
    return None


def generate_explanation(candidate_row: dict, candidate_profile: dict) -> dict:
    """
    Build one explanation object for a candidate.

    Combines title, skills, domain fit, and talent signals into 3-5 bullets.
    """
    title = candidate_row.get("title") or candidate_profile.get("profile", {}).get(
        "current_title", "N/A"
    )
    top_skills = get_top_skills(candidate_profile, limit=TOP_SKILL_COUNT)

    bullets = []

    # Rule 1: Title relevance.
    title_bullet = explain_title(str(title))
    if title_bullet:
        bullets.append(title_bullet)

    # Rule 2: Skill relevance.
    skills_bullet = explain_skills(top_skills)
    if skills_bullet:
        bullets.append(skills_bullet)

    # Rule 3: Domain fit score.
    domain_bullet = explain_domain_fit(candidate_row.get("domain_fit_score", 0.0))
    if domain_bullet:
        bullets.append(domain_bullet)

    # Rule 4: Talent score.
    talent_bullet = explain_talent(candidate_row.get("talent_score", 0.0))
    if talent_bullet:
        bullets.append(talent_bullet)

    # Rule 5: Semantic similarity score.
    similarity_bullet = explain_similarity(candidate_row.get("similarity_score", 0.0))
    if similarity_bullet:
        bullets.append(similarity_bullet)

    # Ensure we always return at least 3 bullets with simple fallbacks.
    if len(bullets) < 3:
        if title and f"Current title: {title}" not in bullets:
            bullets.append(f"Current title: {title}")
    if len(bullets) < 3 and top_skills:
        bullets.append(f"Top skills: {_join_skill_names(top_skills[:3])}")
    if len(bullets) < 3:
        bullets.append("Selected as a top semantic match for this role")

    # Keep only 3 to 5 explanation bullets.
    bullets = bullets[:5]
    if len(bullets) < 3:
        bullets = bullets + ["Potential fit based on overall ranking signals"] * (3 - len(bullets))

    return {
        "candidate_id": candidate_row["candidate_id"],
        "title": str(title),
        "explanation": bullets[:5],
    }


def save_explanations(explanations: list, output_path: str) -> None:
    """Save explanation objects to JSON."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as output_file:
        json.dump(explanations, output_file, indent=2, ensure_ascii=False)


def print_explanations(explanations: list, top_n: int = PRINT_TOP_N) -> None:
    """Print explanations for the top N candidates."""
    print(f"\nTop {top_n} Candidate Explanations")
    print("=" * 60)

    for index, item in enumerate(explanations[:top_n], start=1):
        print(f"\n{index}. {item['candidate_id']} — {item['title']}")
        print("-" * 50)
        for bullet in item["explanation"]:
            print(f"  • {bullet}")


if __name__ == "__main__":
    print("=" * 60)
    print("Candidate Explanation Generator")
    print("=" * 60)
    print(f"Semantic results: {SEMANTIC_RESULTS_FILE}")
    print(f"Top 5000 CSV    : {TOP_5000_FILE}")
    print(f"Candidates JSONL: {CANDIDATES_FILE}")
    print(f"Output JSON     : {OUTPUT_FILE}")
    print()

    try:
        # Step 1: Load top 20 semantic search candidates.
        top_candidates = load_top_semantic_candidates(SEMANTIC_RESULTS_FILE, TOP_N)
        if not top_candidates:
            raise ValueError("No candidates found in semantic results file.")

        candidate_ids = {row["candidate_id"] for row in top_candidates}
        print(f"Loaded {len(top_candidates)} candidates to explain.")

        # Step 2: Load supplementary metadata from top 5000 CSV (fallback enrichment).
        top_5000_metadata = load_top_5000_metadata(TOP_5000_FILE)
        print(f"Loaded supplementary metadata for {len(top_5000_metadata):,} candidates.")

        # Enrich semantic rows with any missing fields from top 5000 data.
        for candidate_row in top_candidates:
            meta = top_5000_metadata.get(candidate_row["candidate_id"], {})
            if not candidate_row.get("title"):
                candidate_row["title"] = meta.get("current_title", "")
            if candidate_row.get("domain_fit_score", 0.0) == 0.0:
                candidate_row["domain_fit_score"] = meta.get("domain_fit_score", 0.0)
            if candidate_row.get("talent_score", 0.0) == 0.0:
                candidate_row["talent_score"] = meta.get("talent_score", 0.0)

        # Step 3: Load full candidate profiles for skill extraction.
        candidate_profiles = load_candidate_profiles(CANDIDATES_FILE, candidate_ids)
        print(f"Loaded {len(candidate_profiles)} candidate profiles from JSONL.")

        missing_ids = candidate_ids - set(candidate_profiles.keys())
        if missing_ids:
            print(f"Warning: {len(missing_ids)} candidate profiles were not found.")

        # Step 4: Generate explanations using rule-based logic.
        explanations = []
        for candidate_row in top_candidates:
            candidate_id = candidate_row["candidate_id"]
            profile = candidate_profiles.get(candidate_id, {})
            explanations.append(generate_explanation(candidate_row, profile))

        # Step 5: Save all explanations to JSON.
        save_explanations(explanations, OUTPUT_FILE)
        print(f"\nSaved {len(explanations)} explanations to: {OUTPUT_FILE}")

        # Step 6: Print explanations for the top 5 candidates.
        print_explanations(explanations, top_n=PRINT_TOP_N)
        print("\n" + "=" * 60)

    except FileNotFoundError as error:
        print(f"ERROR: {error}")
    except (ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}")
    except OSError as error:
        print(f"ERROR: Could not read/write files. {error}")
