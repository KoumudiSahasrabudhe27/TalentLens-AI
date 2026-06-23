"""
backend/app.py

FastAPI application that exposes TalentLens-AI ranking results through a REST API.
Run with: uvicorn backend.app:app --reload
"""

import json
import os
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FINAL_RANKED_FILE = os.path.join(PROJECT_ROOT, "outputs", "final_ranked_candidates.json")
EXPLAINED_CANDIDATES_FILE = os.path.join(
    PROJECT_ROOT, "outputs", "final_ranked_candidates_explained.json"
)
CANDIDATES_JSONL = os.path.join(PROJECT_ROOT, "data", "raw", "candidates.jsonl")

TOTAL_CANDIDATES_ANALYZED = 100_000
RETRIEVED_CANDIDATES = 5_000

CANDIDATES_DATA: List[Dict[str, Any]] = []
DASHBOARD_SUMMARY: Dict[str, Any] = {}

app = FastAPI(
    title="TalentLens-AI API",
    description="Recruiter ranking engine for the Redrob x Hack2Skill challenge.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _safe_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def calculate_confidence(
    domain_fit_score: float,
    talent_score: float,
    semantic_similarity: float,
) -> float:
    """Recruiter confidence score (0-100 scale)."""
    return round(
        (0.5 * domain_fit_score)
        + (0.3 * talent_score)
        + (0.2 * semantic_similarity * 100),
        2,
    )


def get_confidence_label(confidence_score: float) -> str:
    if confidence_score >= 95:
        return "Excellent Match"
    if confidence_score >= 85:
        return "Strong Match"
    if confidence_score >= 75:
        return "Good Match"
    return "Moderate Match"


def get_top_skills(candidate: Dict[str, Any], limit: int = 5) -> List[str]:
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


def detect_hiring_risks(candidate: Dict[str, Any]) -> List[str]:
    """Rule-based hiring risk flags from redrob_signals."""
    signals = candidate.get("redrob_signals", {})
    if not isinstance(signals, dict):
        signals = {}

    risks = []

    notice_period_days = int(_safe_float(signals.get("notice_period_days")))
    if notice_period_days > 60:
        risks.append("Long notice period")

    response_rate = _safe_float(signals.get("recruiter_response_rate"))
    if response_rate < 0.4:
        risks.append("Low recruiter response rate")

    if signals.get("open_to_work_flag") is False:
        risks.append("Not open to work")

    interview_rate = _safe_float(signals.get("interview_completion_rate"))
    if interview_rate < 0.5:
        risks.append("Low interview completion rate")

    return risks


def generate_recruiter_insight(
    title: str,
    top_skills: List[str],
    years_of_experience: float,
    domain_fit_score: float,
    talent_score: float,
) -> str:
    """Generate a concise recruiter-facing insight paragraph."""
    skill_text = ", ".join(top_skills[:4]) if top_skills else "relevant technical skills"
    years_text = f"{years_of_experience:.1f}".rstrip("0").rstrip(".")

    if years_of_experience > 0:
        experience_sentence = f"with {years_text} years of experience"
    else:
        experience_sentence = "with demonstrated professional experience"

    opening = (
        f'This candidate demonstrates strong expertise in {skill_text} '
        f'{experience_sentence} as a {title}. '
    )

    if domain_fit_score >= 80 and talent_score >= 70:
        closing = (
            "High domain alignment and strong hiring signals make them a "
            "recommended candidate for recruiter outreach."
        )
    elif domain_fit_score >= 65:
        closing = (
            "Good domain alignment and hiring signals suggest they are worth "
            "prioritizing for recruiter screening."
        )
    else:
        closing = (
            "Moderate alignment indicates potential fit, but additional "
            "validation through technical interviews is recommended."
        )

    return opening + closing


def load_candidate_profiles(jsonl_path: str, candidate_ids: set) -> Dict[str, Dict[str, Any]]:
    profiles: Dict[str, Dict[str, Any]] = {}

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


def load_json_list(file_path: str) -> List[Dict[str, Any]]:
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as json_file:
        data = json.load(json_file)

    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON list in {file_path}")

    return data


def build_enriched_candidates() -> List[Dict[str, Any]]:
    """Merge ranking outputs, explanations, and profile data."""
    ranked_candidates = load_json_list(FINAL_RANKED_FILE)
    explained_candidates = load_json_list(EXPLAINED_CANDIDATES_FILE)

    explanations_by_id = {
        item["candidate_id"]: item.get("explanations", [])
        for item in explained_candidates
        if item.get("candidate_id")
    }

    candidate_ids = {
        item["candidate_id"] for item in ranked_candidates if item.get("candidate_id")
    }
    profiles = load_candidate_profiles(CANDIDATES_JSONL, candidate_ids)

    enriched = []

    for ranked in ranked_candidates:
        candidate_id = ranked.get("candidate_id")
        profile = profiles.get(candidate_id, {})
        profile_data = profile.get("profile", {}) if isinstance(profile.get("profile"), dict) else {}

        title = ranked.get("current_title") or profile_data.get("current_title", "N/A")
        domain_fit_score = _safe_float(ranked.get("domain_fit_score"))
        talent_score = _safe_float(ranked.get("talent_score"))
        semantic_similarity = _safe_float(ranked.get("semantic_similarity"))
        years_of_experience = _safe_float(profile_data.get("years_of_experience"))
        top_skills = get_top_skills(profile)

        confidence_score = calculate_confidence(
            domain_fit_score, talent_score, semantic_similarity
        )
        hiring_risks = detect_hiring_risks(profile)

        enriched.append(
            {
                "rank": ranked.get("rank"),
                "candidate_id": candidate_id,
                "title": title,
                "current_company": profile_data.get("current_company", "N/A"),
                "years_of_experience": years_of_experience,
                "top_skills": top_skills,
                "final_score": ranked.get("final_score"),
                "semantic_similarity": round(semantic_similarity, 4),
                "domain_fit_score": round(domain_fit_score, 2),
                "talent_score": round(talent_score, 2),
                "confidence_score": confidence_score,
                "confidence_label": get_confidence_label(confidence_score),
                "hiring_risks": hiring_risks,
                "recruiter_insight": generate_recruiter_insight(
                    str(title),
                    top_skills,
                    years_of_experience,
                    domain_fit_score,
                    talent_score,
                ),
                "explanations": explanations_by_id.get(candidate_id, []),
            }
        )

    return enriched


def build_dashboard_summary(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    top_match_score = 0.0
    if candidates:
        top_match_score = max(_safe_float(item.get("final_score")) for item in candidates)

    return {
        "total_candidates_analyzed": TOTAL_CANDIDATES_ANALYZED,
        "retrieved_candidates": RETRIEVED_CANDIDATES,
        "final_ranked_candidates": len(candidates),
        "top_match_score": round(top_match_score, 2),
    }


@app.on_event("startup")
def startup_event() -> None:
    global CANDIDATES_DATA, DASHBOARD_SUMMARY

    print("=" * 60)
    print("TalentLens-AI API starting...")
    print("=" * 60)

    try:
        CANDIDATES_DATA = build_enriched_candidates()
        DASHBOARD_SUMMARY = build_dashboard_summary(CANDIDATES_DATA)
        print(f"Loaded {len(CANDIDATES_DATA)} enriched ranked candidates.")
        print("API is ready.")
        print("Docs available at: http://127.0.0.1:8000/docs")
        print("=" * 60)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as error:
        CANDIDATES_DATA = []
        DASHBOARD_SUMMARY = {}
        print(f"WARNING: Could not load candidate data. {error}")
        print("=" * 60)


@app.get("/")
def root() -> Dict[str, str]:
    return {"status": "running", "project": "TalentLens-AI"}


@app.get("/top-candidates")
def get_top_candidates() -> Dict[str, Any]:
    if not CANDIDATES_DATA:
        raise HTTPException(
            status_code=503,
            detail="Candidate rankings are not loaded. Run the ranking pipeline first.",
        )

    return {
        "summary": DASHBOARD_SUMMARY,
        "candidates": CANDIDATES_DATA,
    }


@app.get("/candidate/{candidate_id}")
def get_candidate(candidate_id: str) -> Dict[str, Any]:
    if not CANDIDATES_DATA:
        raise HTTPException(
            status_code=503,
            detail="Candidate rankings are not loaded. Run the ranking pipeline first.",
        )

    for candidate in CANDIDATES_DATA:
        if candidate.get("candidate_id") == candidate_id:
            return candidate

    raise HTTPException(
        status_code=404,
        detail=f"Candidate not found: {candidate_id}",
    )
