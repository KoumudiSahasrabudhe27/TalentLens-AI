"""
candidate_summary.py

Builds a single clean paragraph from a candidate profile.
This text is useful for semantic search and embedding models.
"""

import json
import os
import re


def _safe_dict(value) -> dict:
    """Return value when it is a dict; otherwise return an empty dict."""
    return value if isinstance(value, dict) else {}


def _safe_list(value) -> list:
    """Return value when it is a list; otherwise return an empty list."""
    return value if isinstance(value, list) else []


def _clean_text(text: str) -> str:
    """Remove extra whitespace so the paragraph stays neat."""
    if not text:
        return ""
    # re.sub replaces repeated whitespace with a single space.
    return re.sub(r"\s+", " ", str(text)).strip()


def _join_phrases(phrases: list) -> str:
    """
    Join short phrases into one readable sentence.

    Example: ["A", "B", "C"] -> "A, B and C"
    """
    phrases = [phrase for phrase in phrases if phrase]
    if not phrases:
        return ""
    if len(phrases) == 1:
        return phrases[0]
    if len(phrases) == 2:
        return f"{phrases[0]} and {phrases[1]}"
    return ", ".join(phrases[:-1]) + f", and {phrases[-1]}"


def _get_top_skill_names(skills: list, limit: int = 10) -> list:
    """
    Return the top skill names sorted by endorsements.

    More endorsements usually means stronger community validation.
    """
    valid_skills = []
    for skill in skills:
        if isinstance(skill, dict) and skill.get("name"):
            endorsements = skill.get("endorsements", 0) or 0
            try:
                endorsements = int(endorsements)
            except (TypeError, ValueError):
                endorsements = 0
            valid_skills.append((skill["name"], endorsements))

    # Sort by endorsements descending, then keep only the skill names.
    valid_skills.sort(key=lambda item: item[1], reverse=True)
    return [name for name, _ in valid_skills[:limit]]


def _format_education_sentence(education_entries: list) -> str:
    """Build one sentence describing the candidate's education."""
    education_phrases = []

    for entry in education_entries:
        if not isinstance(entry, dict):
            continue

        degree = _clean_text(entry.get("degree", ""))
        field_of_study = _clean_text(entry.get("field_of_study", ""))
        institution = _clean_text(entry.get("institution", ""))

        if degree and field_of_study and institution:
            education_phrases.append(f"a {degree} in {field_of_study} from {institution}")
        elif degree and institution:
            education_phrases.append(f"a {degree} from {institution}")
        elif institution:
            education_phrases.append(f"studies at {institution}")

    if not education_phrases:
        return ""

    if len(education_phrases) == 1:
        return f"Holds {education_phrases[0]}."

    return f"Holds {_join_phrases(education_phrases)}."


def _format_career_highlights(career_history: list) -> str:
    """
    Build a sentence about previous roles (not the current job).

    We skip entries where is_current is True.
    """
    previous_roles = []

    for role in career_history:
        if not isinstance(role, dict):
            continue

        # Current role is usually marked with is_current=True.
        if role.get("is_current") is True:
            continue

        title = _clean_text(role.get("title", ""))
        company = _clean_text(role.get("company", ""))

        if title and company:
            previous_roles.append(f"{title} at {company}")
        elif title:
            previous_roles.append(title)

    if not previous_roles:
        return ""

    return f"Previously worked as {_join_phrases(previous_roles)}."


def generate_candidate_summary(candidate: dict) -> str:
    """
    Generate one paragraph summarizing a candidate profile.

    Args:
        candidate: A single candidate object from candidates.jsonl.

    Returns:
        A clean text paragraph suitable for semantic search and embeddings.
    """
    if not isinstance(candidate, dict):
        candidate = {}

    # Read the main sections from the candidate record.
    profile = _safe_dict(candidate.get("profile"))
    skills = _safe_list(candidate.get("skills"))
    education = _safe_list(candidate.get("education"))
    career_history = _safe_list(candidate.get("career_history"))

    sentences = []

    # --- 1. Current title, years of experience, and current company ---
    # Example: "Backend Engineer with 6.9 years of experience at Mindtree."
    current_title = _clean_text(profile.get("current_title", "")) or "Professional"
    years_of_experience = profile.get("years_of_experience")
    current_company = _clean_text(profile.get("current_company", ""))

    if years_of_experience is not None:
        try:
            years_text = f"{float(years_of_experience):g}"
        except (TypeError, ValueError):
            years_text = str(years_of_experience)
    else:
        years_text = ""

    if years_text and current_company:
        sentences.append(
            f"{current_title} with {years_text} years of experience at {current_company}."
        )
    elif years_text:
        sentences.append(f"{current_title} with {years_text} years of experience.")
    elif current_company:
        sentences.append(f"{current_title} at {current_company}.")
    else:
        sentences.append(f"{current_title}.")

    # --- 2. Top 10 skills ---
    # Example: "Experienced in Spark, Airflow, SQL and data infrastructure."
    top_skills = _get_top_skill_names(skills, limit=10)
    if top_skills:
        sentences.append(f"Experienced in {_join_phrases(top_skills)}.")

    # --- 3. Professional summary ---
    # This is the candidate's own description of their background and interests.
    professional_summary = _clean_text(profile.get("summary", ""))
    if professional_summary:
        # Ensure the summary ends with a period for consistent paragraph flow.
        if not professional_summary.endswith("."):
            professional_summary += "."
        sentences.append(professional_summary)

    # --- 4. Education ---
    # Example: "Holds a B.E. in Computer Science from Lovely Professional University."
    education_sentence = _format_education_sentence(education)
    if education_sentence:
        sentences.append(education_sentence)

    # --- 5. Career history highlights ---
    # Example: "Previously worked as Analytics Engineer at Dunder Mifflin."
    career_sentence = _format_career_highlights(career_history)
    if career_sentence:
        sentences.append(career_sentence)

    # Join all parts into one paragraph with spaces between sentences.
    summary = " ".join(sentences)
    return _clean_text(summary)


if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    data_file = os.path.join(project_root, "data", "raw", "candidates.jsonl")
    output_file = os.path.join(project_root, "outputs", "sample_candidate_summary.txt")

    print("=" * 60)
    print("Candidate Summary - Test Run")
    print("=" * 60)

    try:
        with open(data_file, "r", encoding="utf-8") as file:
            first_line = file.readline()

        if not first_line.strip():
            raise ValueError(f"No data found in {data_file}")

        candidate = json.loads(first_line)
        candidate_id = candidate.get("candidate_id", "N/A")
        summary = generate_candidate_summary(candidate)

        print(f"\nCandidate ID: {candidate_id}\n")
        print("Generated Summary")
        print("-" * 17)
        print(summary)
        print()

        # Ensure the outputs folder exists before saving the file.
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as output:
            output.write(summary)

        print(f"Saved summary to: {output_file}")
        print("=" * 60)

    except FileNotFoundError:
        print(f"ERROR: Could not find dataset file at {data_file}")
    except json.JSONDecodeError as error:
        print(f"ERROR: Invalid JSON on the first line of {data_file}")
        print(error)
    except (ValueError, OSError) as error:
        print(f"ERROR: {error}")
