"""
explore_dataset.py

A beginner-friendly script to peek at one candidate record from the
TalentLens-AI dataset. Data engineers often start by reading a single row
before building full ingestion pipelines.
"""

# Import the built-in json module so we can read JSON Lines (.jsonl) files.
import json

# Import os.path so we can build file paths in a way that works on any OS.
import os

# Import sys so we can exit the program with a clear error message if needed.
import sys


# Store the path to the raw candidate file relative to this script's location.
# os.path.dirname(__file__) finds the folder where this .py file lives.
# os.path.join(...) safely joins folder names into one path string.
DATA_FILE = os.path.join(
    os.path.dirname(__file__),
    "data",
    "raw",
    "candidates.jsonl",
)


def read_first_candidate(file_path: str) -> dict:
    """
    Open a JSONL file and return only the first candidate record as a Python dict.

    JSONL (JSON Lines) means each line in the file is one complete JSON object.
  This is common in data engineering because you can stream large files line by line
    instead of loading everything into memory at once.
    """
    # Check whether the file exists before we try to open it.
    if not os.path.isfile(file_path):
        # Raise a clear error that our main() function can catch and display.
        raise FileNotFoundError(
            f"Dataset file not found: {file_path}\n"
            "Make sure candidates.jsonl is inside data/raw/."
        )

    # Open the file in read mode ("r") with UTF-8 encoding for international text.
    # The "with" block automatically closes the file when we are done.
    with open(file_path, "r", encoding="utf-8") as file:
        # Read just the first line from the file.
        first_line = file.readline()

        # If the first line is empty, the file has no data to explore.
        if not first_line.strip():
            raise ValueError(
                f"The file exists but is empty: {file_path}\n"
                "Add at least one candidate record to explore."
            )

        # Convert the JSON text on that line into a Python dictionary.
        try:
            candidate = json.loads(first_line)
        except json.JSONDecodeError as error:
            # If the line is not valid JSON, explain what went wrong.
            raise ValueError(
                f"Could not parse the first line as JSON in {file_path}.\n"
                f"Details: {error}"
            ) from error

    # Return the parsed candidate record to the caller.
    return candidate


def get_nested_value(data: dict, *keys, default=None):
    """
    Safely read nested dictionary values without crashing if a key is missing.

    Example: get_nested_value(candidate, "profile", "current_title")
    walks into candidate["profile"]["current_title"] step by step.
    """
    # Start at the top-level dictionary.
    current = data

    # Walk through each key in order (e.g., "profile", then "current_title").
    for key in keys:
        # If the current level is not a dictionary, we cannot go deeper.
        if not isinstance(current, dict):
            return default

        # Try to move one level deeper; return default if the key is missing.
        current = current.get(key, default)

        # Stop early if we already hit a missing value.
        if current is default:
            return default

    return current


def extract_skill_names(skills) -> list:
    """
    Pull skill names out of the skills list.

    In this dataset, each skill is an object like:
    {"name": "Python", "proficiency": "advanced", ...}
    """
    # If skills is missing or not a list, return an empty list safely.
    if not isinstance(skills, list):
        return []

    skill_names = []

    # Loop through each skill entry one at a time.
    for skill in skills:
        # Only read the name when the entry is a dictionary with a "name" key.
        if isinstance(skill, dict) and "name" in skill:
            skill_names.append(skill["name"])

    return skill_names


def print_section(title: str) -> None:
    """Print a small section header to keep terminal output easy to scan."""
    print()
    print(title)
    print("-" * len(title))


def explore_candidate(candidate: dict) -> None:
    """Print a clean summary of the most important fields from one candidate."""
    # Read top-level fields from the candidate record.
    candidate_id = candidate.get("candidate_id", "N/A")

    # current_title and years_of_experience live inside the nested "profile" object.
    current_title = get_nested_value(candidate, "profile", "current_title", default="N/A")
    years_of_experience = get_nested_value(
        candidate, "profile", "years_of_experience", default="N/A"
    )

    # These fields are lists, so len(...) tells us how many entries each has.
    career_history = candidate.get("career_history", [])
    education = candidate.get("education", [])
    skills = candidate.get("skills", [])

    # Count list items only when the field is actually a list.
    career_count = len(career_history) if isinstance(career_history, list) else 0
    education_count = len(education) if isinstance(education, list) else 0
    skills_count = len(skills) if isinstance(skills, list) else 0

    # redrob_signals is a dictionary of platform activity metrics.
    redrob_signals = candidate.get("redrob_signals", {})
    if not isinstance(redrob_signals, dict):
        redrob_signals = {}

    # Convert skill objects into a simple list of skill name strings.
    skill_names = extract_skill_names(skills)

    # Print a friendly overview for the learner.
    print("=" * 60)
    print("TalentLens-AI Dataset Explorer")
    print("Showing the FIRST candidate from candidates.jsonl")
    print("=" * 60)

    print_section("Basic Profile")
    print(f"Candidate ID         : {candidate_id}")
    print(f"Current Title        : {current_title}")
    print(f"Years of Experience  : {years_of_experience}")
    print(f"Career History Count : {career_count}")
    print(f"Education Count      : {education_count}")
    print(f"Skills Count         : {skills_count}")

    print_section("Redrob Signals Keys")
    if redrob_signals:
        # sorted(...) prints keys in alphabetical order for easier reading.
        for index, key in enumerate(sorted(redrob_signals.keys()), start=1):
            print(f"{index:>2}. {key}")
    else:
        print("No redrob_signals data found for this candidate.")

    print_section("First 10 Skill Names")
    if skill_names:
        # Show at most 10 skills using list slicing: skill_names[:10]
        for index, skill_name in enumerate(skill_names[:10], start=1):
            print(f"{index:>2}. {skill_name}")

        # If there are fewer than 10 skills, mention that clearly.
        if len(skill_names) < 10:
            print(f"\nOnly {len(skill_names)} skill(s) available in this record.")
    else:
        print("No skills found for this candidate.")

    print()
    print("Exploration complete.")
    print("=" * 60)


def main() -> int:
    """
    Main entry point for the script.

    Returning 0 means success; returning 1 means the script failed.
    This pattern is useful when chaining scripts in data pipelines.
    """
    try:
        # Step 1: Read only the first candidate from the JSONL file.
        candidate = read_first_candidate(DATA_FILE)

        # Step 2: Make sure we actually received a dictionary object.
        if not isinstance(candidate, dict):
            raise TypeError(
                "The first line was valid JSON, but it was not a JSON object (dict)."
            )

        # Step 3: Print the exploration summary in a readable format.
        explore_candidate(candidate)

        # Return 0 to tell the operating system that everything worked.
        return 0

    except FileNotFoundError as error:
        # Handle missing file errors with a helpful message.
        print("ERROR: File not found.", file=sys.stderr)
        print(error, file=sys.stderr)
        return 1

    except (ValueError, TypeError, json.JSONDecodeError) as error:
        # Handle bad/empty data or parsing problems.
        print("ERROR: Could not explore the dataset.", file=sys.stderr)
        print(error, file=sys.stderr)
        return 1

    except OSError as error:
        # Handle general file system issues (permissions, disk errors, etc.).
        print("ERROR: Problem reading the dataset file.", file=sys.stderr)
        print(error, file=sys.stderr)
        return 1


# This block runs only when you execute: python explore_dataset.py
if __name__ == "__main__":
    # sys.exit(...) passes our return code back to the terminal/shell.
    sys.exit(main())
