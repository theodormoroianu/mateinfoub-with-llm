import logging
import json
from typing import Tuple
import glob

import internal_types

ANSWERS_MATCHING_FILE = internal_types.SOLUTIONS_DIR / "answers_matching.json"


def compare_answers(
    good_answer: str, provided_answer: str, ask_user: bool = False
) -> bool:
    """
    Check if two answers are equivalent. Ask the user if unable to determine automatically.
    """

    # Load the database of known answers.
    matching, non_matching = load_answers_db()

    # Check if the answer is in the database.
    if [good_answer, provided_answer] in matching:
        return True
    elif [good_answer, provided_answer] in non_matching:
        return False

    # Same answer.
    if good_answer == provided_answer:
        return True

    # Failed to get answer.
    if provided_answer == "Failed to get answer." or provided_answer == "Timeout":
        return False

    if provided_answer.strip() == "":
        # If the provided answer is empty, we can consider it wrong.
        return False

    # We can convert the good answer and the provided one to a number.
    try:
        good_answer = float(good_answer)
        provided_answer = float(provided_answer)

        # If difference is small, consider it the same.
        return abs(good_answer - provided_answer) < 0.01

    except Exception:
        pass

    # If we are not allowed to ask the user, return an exception.
    if not ask_user:
        raise Exception(
            f"Answers are not the same, but we are not allowed to ask the user: {good_answer} != {provided_answer}"
        )

    # If we are allowed to ask the user, we need to ask them.
    print(f"Good answer:     {good_answer}")
    print(f"Provided answer: {provided_answer}")
    print("Are these two answers equivalent? (y/n)")
    answer = input("> ").strip().lower()

    if answer == "y":
        return True
    elif answer == "n":
        return False
    else:
        raise Exception("Invalid answer. Please answer with 'y' or 'n'.")


def load_answers_db() -> Tuple[list[Tuple[int, int]], list[Tuple[int, int]]]:
    """
    Loads a JSON file with known answers.

    This returns:
    1. The list of matching answers.
    2. The list of non-matching answers.
    """
    if not ANSWERS_MATCHING_FILE.exists():
        # Create the file if it doesn't exist.
        with open(ANSWERS_MATCHING_FILE, "w") as f:
            f.write(json.dumps({"matching": [], "non_matching": []}, indent=2))

    data = json.loads(open(ANSWERS_MATCHING_FILE, "r").read())
    return data["matching"], data["non_matching"]


def save_answers_db(
    matching: list[Tuple[int, int]], non_matching: list[Tuple[int, int]]
):
    """
    Saves the answers to a JSON file.
    """
    data = {
        "matching": matching,
        "non_matching": non_matching,
    }
    with open(ANSWERS_MATCHING_FILE, "w") as f:
        f.write(json.dumps(data, indent=2))


def load_good_answers_and_provided_answers() -> list[Tuple[str, str]]:
    """
    Load the good answers and the provided answers from the JSON files.
    """

    answers = []

    for lang in ["en", "ro"]:
        file_data = internal_types.get_solution_files_no_multiple_choices_glob()
        files = glob.glob(file_data[lang])
        contests = internal_types.Contest.read_all_contests()[lang]

        for file in files:
            with open(file, "r") as f:
                solutions = [
                    internal_types.LLMAnswer.from_json(s) for s in json.loads(f.read())
                ]
                for solution in solutions:
                    # Get the contest and question number.
                    contest = [c for c in contests if c.name == solution.edition]
                    assert len(contest) == 1, f"Contest {solution.edition} not found."
                    contest = contest[0]

                    question = contest.problems[solution.problem_index]
                    answers.append([question.correct_answer, solution.answer])
    return answers


def compute_matchings_for_answers():
    """
    For the "no multiple choice" experiment, the LLMs are not provided with the multiple choice options.
    This makes testing the answers a bit harder, as we cannot rely on automatic verification anymore.

    This function uses a database of known answers to verify if the answer provided by the LLM is correct.
    """
    # Load the dict.
    matching, non_matching = load_answers_db()

    # Load the answers.
    answers = load_good_answers_and_provided_answers()

    def filter_answers(answers: list[Tuple[str, str]]) -> list[Tuple[str, str]]:
        """
        Filter answers to remove stuff we know is correct or not.
        """
        return [i for i in answers if i not in matching and i not in non_matching]

    answers = filter_answers(answers)
    print(f"There are {len(answers)} answers to check.")

    while len(answers) > 0:
        if len(answers) % 10 == 0:
            print(f"There are {len(answers)} answers to check.")

        if compare_answers(answers[0][0], answers[0][1], True):
            if answers[0] not in matching:
                matching.append(answers[0])
        else:
            if answers[0] not in non_matching:
                non_matching.append(answers[0])

        answers = filter_answers(answers)
        save_answers_db(matching, non_matching)
