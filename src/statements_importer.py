import json
import pathlib
import sys

from tqdm import tqdm

import internal_types
import llm_interactor

def convert_statements(force: bool = False):
    """
    Ingest data from the format it is stored
    """
    # Where the data lives.
    this_dir = pathlib.Path(__file__).parent
    data_dir = this_dir.parent / "data"

    # Original statements.
    ro_statements = data_dir / "ro_statements.json"
    
    # Translated statements.
    en_statements = data_dir / "en_statements.json"
    
    
    if not ro_statements.exists():
        print(f"Could not find {ro_statements}. Please create the file and add data (for instance from https://mateinfo-ub.github.io/#/toate-datele).")
        sys.exit(0)

    if en_statements.exists() and not force:
        print(f"{en_statements} already exists. If you want to overwrite it, use --force.")
        sys.exit(0)

    # Load the data.
    with open(ro_statements, "r") as f:
        content = json.loads(f.read())
        ro_data: list[internal_types.Contest] = [
            internal_types.Contest.from_romanian_json(c)
            for c in content
        ]
    
    # Convert to English.
    print("Translating to English...")
    en_data: list[internal_types.Contest] = []
    for nr, ro_contest in enumerate(ro_data):
        print(f"Contest {nr + 1}/{len(ro_data)}")
        en_problems: list[internal_types.Problem] = []
        for ro_problem in tqdm(ro_contest.problems):
            en_statement = llm_interactor.translate_ro_to_en(ro_problem.markdown_statement)
            if ro_problem.image_content:
                en_image_content = llm_interactor.translate_ro_to_en(ro_problem.image_content)
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
    with open(en_statements, "w") as f:
        f.write(json.dumps([c.to_english_json() for c in en_data], indent=4))
    print(f"Saved to {en_statements}")    
