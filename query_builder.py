"""
query_builder.py

Builds a semantic search query from parsed job description data.
A focused natural-language query often works better than raw JD text for embeddings.
"""

import json
import os


PROJECT_ROOT = os.path.dirname(__file__)

PARSED_JD_FILE = os.path.join(PROJECT_ROOT, "outputs", "parsed_jd.json")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "outputs", "search_query.txt")

# Maximum allowed query length for embedding models and readability.
MAX_QUERY_LENGTH = 500

# Map short skill names to clearer phrases for the search query.
SKILL_PHRASES = {
    "retrieval": "retrieval systems",
    "ranking": "ranking algorithms",
    "search": "semantic search",
    "recommendation": "recommendation systems",
    "matching": "candidate matching",
    "embeddings": "embeddings",
    "vector databases": "vector databases",
    "vector database": "vector databases",
    "python": "Python",
    "llm": "LLM systems",
    "llms": "LLM systems",
    "evaluation": "evaluation frameworks",
    "relevance": "relevance modeling",
    "faiss": "FAISS",
    "milvus": "Milvus",
    "pinecone": "Pinecone",
    "weaviate": "Weaviate",
    "qdrant": "Qdrant",
}

# Specific vector DB tools — if any appear, we can add one summary phrase.
VECTOR_DB_TOOLS = {"faiss", "milvus", "pinecone", "weaviate", "qdrant"}


def load_parsed_jd(file_path: str) -> dict:
    """Load structured JD data from parsed_jd.json."""
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Parsed JD file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as input_file:
        data = json.load(input_file)

    if not isinstance(data, dict):
        raise ValueError("parsed_jd.json must contain a JSON object.")

    return data


def _normalize_term(term: str) -> str:
    """Normalize a term for duplicate detection."""
    return term.strip().lower()


def _to_phrase(term: str) -> str:
    """Convert a skill/keyword into a readable query phrase."""
    normalized = _normalize_term(term)
    return SKILL_PHRASES.get(normalized, term.strip())


def _build_role_prefix(preferred_titles: list) -> str:
    """
    Build the opening role phrase from preferred titles.

    Example: "Senior AI Engineer"
    """
    if not preferred_titles:
        return "Senior AI Engineer"

    primary_title = preferred_titles[0].strip()

    # Add "Senior" when it is not already part of the title.
    if primary_title.lower().startswith("senior"):
        return primary_title

    return f"Senior {primary_title}"


def _collect_expertise_phrases(skills: list, keywords: list) -> list:
    """
    Collect unique expertise phrases from skills and keywords.

    Skills are added first, then keywords fill in anything missing.
    Individual vector DB names are skipped here and summarized later.
    """
    seen_terms = set()
    phrases = []
    has_vector_db_tool = False

    # Process skills first (core requirements), then keywords (importance order).
    for term in list(skills) + list(keywords):
        normalized = _normalize_term(term)
        if not normalized or normalized in seen_terms:
            continue

        seen_terms.add(normalized)

        # Track vector DB tools so we can add one combined phrase later.
        if normalized in VECTOR_DB_TOOLS:
            has_vector_db_tool = True
            continue

        # Skip title terms here; they are used in the role prefix.
        if normalized == "ai engineer":
            continue

        phrases.append(_to_phrase(term))

    # Add one broad infrastructure phrase if specific DB tools were found.
    if has_vector_db_tool and "production search infrastructure" not in [
        phrase.lower() for phrase in phrases
    ]:
        phrases.append("production search infrastructure")

    return phrases


def _join_phrases(phrases: list) -> str:
    """
    Join phrases into natural English.

    Example: "A, B, C and D"
    """
    if not phrases:
        return "AI and search systems"

    if len(phrases) == 1:
        return phrases[0]

    if len(phrases) == 2:
        return f"{phrases[0]} and {phrases[1]}"

    return ", ".join(phrases[:-1]) + f" and {phrases[-1]}"


def _trim_query_to_limit(query: str, max_length: int) -> str:
    """
    Shorten the query if it exceeds the character limit.

    We remove phrases from the end until the query fits.
    """
    if len(query) <= max_length:
        return query

    # Split the expertise section and remove trailing phrases.
    prefix = " with expertise in "
    if prefix not in query:
        return query[: max_length - 3].rstrip() + "..."

    role_part, expertise_part = query.split(prefix, max_length=1)
    expertise_part = expertise_part.rstrip(".")

    phrases = [phrase.strip() for phrase in expertise_part.split(",")]

    while phrases and len(query) > max_length:
        phrases.pop()
        if not phrases:
            query = role_part + "."
            break
        expertise_text = _join_phrases(phrases)
        query = f"{role_part}{prefix}{expertise_text}."

    if len(query) > max_length:
        query = query[: max_length - 3].rstrip() + "..."

    return query


def build_search_query(parsed_jd: dict) -> str:
    """
    Build one clean semantic search query from parsed JD fields.

    Uses skills, preferred_titles, and keywords from parsed_jd.json.
    """
    skills = parsed_jd.get("skills", [])
    preferred_titles = parsed_jd.get("preferred_titles", [])
    keywords = parsed_jd.get("keywords", [])

    if not isinstance(skills, list):
        skills = []
    if not isinstance(preferred_titles, list):
        preferred_titles = []
    if not isinstance(keywords, list):
        keywords = []

    role_prefix = _build_role_prefix(preferred_titles)
    expertise_phrases = _collect_expertise_phrases(skills, keywords)
    expertise_text = _join_phrases(expertise_phrases)

    query = f"{role_prefix} with expertise in {expertise_text}."
    query = _trim_query_to_limit(query, MAX_QUERY_LENGTH)

    return query


def save_search_query(query: str, output_path: str) -> None:
    """Save the generated query to a text file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as output_file:
        output_file.write(query)


if __name__ == "__main__":
    print("=" * 60)
    print("Query Builder")
    print("=" * 60)
    print(f"Input : {PARSED_JD_FILE}")
    print(f"Output: {OUTPUT_FILE}")
    print()

    try:
        # Step 1: Load parsed JD data.
        parsed_jd = load_parsed_jd(PARSED_JD_FILE)

        # Step 2: Build one clean semantic search query.
        search_query = build_search_query(parsed_jd)

        # Step 3: Save query to text file.
        save_search_query(search_query, OUTPUT_FILE)

        # Step 4: Print results.
        print("Generated Query")
        print("-" * 15)
        print(search_query)
        print()
        print(f"Query length: {len(search_query)} characters")
        print(f"Saved to    : {OUTPUT_FILE}")
        print("=" * 60)

    except FileNotFoundError as error:
        print(f"ERROR: {error}")
    except (ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}")
    except OSError as error:
        print(f"ERROR: Could not read/write files. {error}")
