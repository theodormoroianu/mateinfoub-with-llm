import json
import pathlib
import sys
import logging

from tqdm import tqdm

import internal_types
import llm_interactor

# Directory where our statements and results are stored.
DATA_DIR = pathlib.Path(__file__).parent.parent / "data" / "statements"

# Original statements.
RO_STATEMENTS_FILE = DATA_DIR / "ro_statements.json"

# Translated statements.
EN_STATEMENTS_FILE = DATA_DIR / "en_statements.json"


def run_models_on_statements():
    """
    Run the models on the statements and save the results.
    """
    if not EN_STATEMENTS_FILE.exists() or not RO_STATEMENTS_FILE.exists():
        logging.error(
            f"Could not find {EN_STATEMENTS_FILE} or {RO_STATEMENTS_FILE}. Please create the files first"
        )
        sys.exit(-1)

    # Load the data.
    with open(EN_STATEMENTS_FILE, "r") as f:
        content = json.loads(f.read())
        en_data: list[internal_types.Contest] = [
            internal_types.Contest.from_english_json(c) for c in content
        ]

    # Run the models.
    print("Running models...")
    for nr, en_contest in enumerate(en_data):
        print(f"Contest {nr + 1}/{len(en_data)}")
        for en_problem in tqdm(en_contest.problems):
            if en_problem.image_content:
                en_problem.image_content = llm_interactor.translate_ro_to_en(
                    en_problem.image_content
                )
            en_problem.markdown_statement = llm_interactor.translate_ro_to_en(
                en_problem.markdown_statement
            )

    # Save the data.
    print("Saving data...")
    with open(EN_STATEMENTS_FILE, "w") as f:
        f.write(json.dumps([c.to_english_json() for c in en_data], indent=2))
    print(f"Saved to {EN_STATEMENTS_FILE}")


def convert_statements(force: bool = False):
    """
    Ingest data from the format it is stored
    """
    if not RO_STATEMENTS_FILE.exists():
        print(
            f"Could not find {RO_STATEMENTS_FILE}. Please create the file and add data (for instance from https://mateinfo-ub.github.io/#/toate-datele)."
        )
        sys.exit(0)

    if EN_STATEMENTS_FILE.exists() and not force:
        print(
            f"{EN_STATEMENTS_FILE} already exists. If you want to overwrite it, use --force."
        )
        sys.exit(0)

    # Load the data.
    with open(RO_STATEMENTS_FILE, "r") as f:
        content = json.loads(f.read())
        ro_data: list[internal_types.Contest] = [
            internal_types.Contest.from_romanian_json(c) for c in content
        ]

    # Convert to English.
    print("Translating to English...")
    en_data: list[internal_types.Contest] = []
    for nr, ro_contest in enumerate(ro_data):
        print(f"Contest {nr + 1}/{len(ro_data)}")
        en_problems: list[internal_types.Problem] = []
        for ro_problem in tqdm(ro_contest.problems):
            en_statement = llm_interactor.translate_ro_to_en(
                ro_problem.markdown_statement
            )
            if ro_problem.image_content:
                en_image_content = llm_interactor.translate_ro_to_en(
                    ro_problem.image_content
                )
            else:
                en_image_content = None
            en_problem = internal_types.Problem(
                title=ro_problem.title,
                markdown_statement=en_statement,
                image_content=en_image_content,
                image_path=ro_problem.image_path,
                answer_variants=ro_problem.answer_variants,
                correct_answer=ro_problem.correct_answer,
                difficulty=ro_problem.difficulty,
            )
            en_problems.append(en_problem)
        en_contest = internal_types.Contest(
            name=ro_contest.name,
            problems=en_problems,
        )
        en_data.append(en_contest)

    # Save the data.
    print("Saving data...")
    with open(EN_STATEMENTS_FILE, "w") as f:
        f.write(json.dumps([c.to_english_json() for c in en_data], indent=2))
    print(f"Saved to {EN_STATEMENTS_FILE}")
