"""
jd_parser.py

Extracts structured hiring signals from a job description text file.
Turning unstructured JD text into JSON makes it easier for ranking systems to use.
"""

import json
import os
import re


PROJECT_ROOT = os.path.dirname(__file__)

JOB_DESCRIPTION_FILE = os.path.join(PROJECT_ROOT, "data", "raw", "job_description.txt")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "outputs", "parsed_jd.json")

# Skills we look for in the job description text.
REQUIRED_SKILLS = [
    "retrieval",
    "ranking",
    "search",
    "recommendation",
    "matching",
    "embeddings",
    "vector databases",
    "faiss",
    "milvus",
    "pinecone",
    "weaviate",
    "qdrant",
    "python",
    "llm",
    "evaluation",
    "relevance",
]

# Job titles that indicate a strong fit for this role.
PREFERRED_TITLES = [
    "Search Engineer",
    "ML Engineer",
    "AI Engineer",
    "Data Engineer",
    "Backend Engineer",
    "Recommendation Engineer",
    "Applied Scientist",
    "Software Engineer",
]

# Alternate spellings / related phrases that should match a skill term.
SKILL_ALIASES = {
    "vector databases": ["vector database", "vector databases"],
    "llm": ["llm", "llms"],
}


def read_job_description(file_path: str) -> str:
    """Read the full job description from a text file."""
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Job description not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as job_file:
        text = job_file.read().strip()

    if not text:
        raise ValueError(f"Job description file is empty: {file_path}")

    return text


def _term_found(term: str, text_lower: str) -> bool:
    """
    Check whether a skill or title appears in the job description.

    Uses simple case-insensitive substring matching, with aliases when needed.
    """
    aliases = SKILL_ALIASES.get(term.lower(), [term.lower()])

    for alias in aliases:
        if alias.lower() in text_lower:
            return True

    return False


def extract_required_skills(job_text: str) -> list:
    """Return required skills that appear in the JD."""
    text_lower = job_text.lower()
    matched_skills = []

    for skill in REQUIRED_SKILLS:
        if _term_found(skill, text_lower):
            matched_skills.append(skill)

    return matched_skills


def extract_preferred_titles(job_text: str) -> list:
    """Return preferred titles that appear in the JD."""
    text_lower = job_text.lower()
    matched_titles = []

    for title in PREFERRED_TITLES:
        if title.lower() in text_lower:
            matched_titles.append(title)

    # The JD title itself is "Senior AI Engineer", so ensure AI Engineer is captured.
    if "ai engineer" in text_lower and "AI Engineer" not in matched_titles:
        matched_titles.append("AI Engineer")

    return matched_titles


def extract_experience_range(job_text: str) -> str:
    """
    Detect the experience range from the JD.

    Looks for patterns like:
      - 5-9 years
      - 5–9 years (en dash)
    """
    # \d+\s*[-–]\s*\d+ matches ranges like 5-9 or 5–9
    range_pattern = re.compile(r"(\d+)\s*[-–]\s*(\d+)\s*years?", re.IGNORECASE)
    match = range_pattern.search(job_text)

    if match:
        start_years = match.group(1)
        end_years = match.group(2)
        return f"{start_years}-{end_years} years"

    return "Not specified"


def count_keyword_mentions(keyword: str, text_lower: str) -> int:
    """Count how many times a keyword appears in the job description."""
    aliases = SKILL_ALIASES.get(keyword.lower(), [keyword.lower()])
    total_count = 0

    for alias in aliases:
        total_count += text_lower.count(alias.lower())

    return total_count


def extract_top_keywords(job_text: str, matched_skills: list, matched_titles: list) -> list:
    """
    Return the most frequently mentioned matched keywords.

    We count mentions for skills and titles, then sort by frequency.
    """
    text_lower = job_text.lower()
    keyword_counts = {}

    # Count skill mentions.
    for skill in matched_skills:
        keyword_counts[skill] = count_keyword_mentions(skill, text_lower)

    # Count title mentions (usually 0 or 1, but still useful to include).
    for title in matched_titles:
        keyword_counts[title] = text_lower.count(title.lower())

    # Sort keywords by mention count (highest first), then alphabetically.
    sorted_keywords = sorted(
        keyword_counts.items(),
        key=lambda item: (-item[1], item[0].lower()),
    )

    # Return only the keyword names, not the counts.
    return [keyword for keyword, _ in sorted_keywords]


def parse_job_description(job_text: str) -> dict:
    """Extract all structured hiring signals from the JD text."""
    skills = extract_required_skills(job_text)
    preferred_titles = extract_preferred_titles(job_text)
    experience = extract_experience_range(job_text)
    keywords = extract_top_keywords(job_text, skills, preferred_titles)

    return {
        "skills": skills,
        "preferred_titles": preferred_titles,
        "experience": experience,
        "keywords": keywords,
    }


def save_parsed_jd(parsed_data: dict, output_path: str) -> None:
    """Save parsed JD data as formatted JSON."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as output_file:
        json.dump(parsed_data, output_file, indent=2, ensure_ascii=False)


def print_parsed_results(parsed_data: dict) -> None:
    """Print parsed JD results in a readable format."""
    print("\nParsed Job Description")
    print("=" * 50)

    print("\nRequired Skills Found")
    print("-" * 21)
    if parsed_data["skills"]:
        for index, skill in enumerate(parsed_data["skills"], start=1):
            print(f"  {index}. {skill}")
    else:
        print("  None found")

    print("\nPreferred Titles Found")
    print("-" * 22)
    if parsed_data["preferred_titles"]:
        for index, title in enumerate(parsed_data["preferred_titles"], start=1):
            print(f"  {index}. {title}")
    else:
        print("  None found")

    print("\nExperience Range")
    print("-" * 16)
    print(f"  {parsed_data['experience']}")

    print("\nTop Matched Keywords")
    print("-" * 20)
    if parsed_data["keywords"]:
        for index, keyword in enumerate(parsed_data["keywords"], start=1):
            print(f"  {index}. {keyword}")
    else:
        print("  None found")

    print("\n" + "=" * 50)


if __name__ == "__main__":
    print("=" * 50)
    print("JD Parser")
    print("=" * 50)
    print(f"Input : {JOB_DESCRIPTION_FILE}")
    print(f"Output: {OUTPUT_FILE}")

    try:
        # Step 1: Read the job description text.
        job_text = read_job_description(JOB_DESCRIPTION_FILE)

        # Step 2: Extract structured hiring signals.
        parsed_data = parse_job_description(job_text)

        # Step 3: Save results to JSON.
        save_parsed_jd(parsed_data, OUTPUT_FILE)

        # Step 4: Print a clear summary in the terminal.
        print_parsed_results(parsed_data)
        print(f"\nSaved parsed JD to: {OUTPUT_FILE}")

    except FileNotFoundError as error:
        print(f"ERROR: {error}")
    except ValueError as error:
        print(f"ERROR: {error}")
    except OSError as error:
        print(f"ERROR: Could not read/write files. {error}")
