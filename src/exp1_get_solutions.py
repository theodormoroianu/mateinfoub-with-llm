import json
import logging

from tqdm import tqdm

import internal_types
import llm_interactor


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def solve_tasks_asking_llms(round: int):
    """
    Asks LLMs to solve the tasks.
    """
    contests = internal_types.Contest.read_all_contests()
    logging.info(f"Round {round}")
    for lang, contests in list(contests.items()):

        save_loc = (
            str(internal_types.RO_SOLUTIONS_FILE) + "_round_" + str(round) + ".json"
            if lang == "ro"
            else str(internal_types.EN_SOLUTIONS_FILE)
            + "_round_"
            + str(round)
            + ".json"
        )
        try:
            with open(save_loc, "r") as f:
                solutions = [
                    internal_types.LLMAnswer.from_json(s) for s in json.loads(f.read())
                ]
        except FileNotFoundError:
            solutions = []

        # Try to fix python extraction from previous runs.
        for s in solutions:
            s.try_extract_python_code()

        logger.info(f"Solving tasks for lang {lang}")
        for contest in contests:
            logger.info(f"Solving tasks for contest {contest.name}")
            for problem_idx, problem in enumerate(tqdm(contest.problems)):
                logger.info(f"Solving task {problem.title}")
                for llm in llm_interactor.Model._member_map_.values():
                    # if llm == llm_interactor.Model.GEMINI_2_5:
                    #     continue

                    # Check if we already have a solution for this problem.
                    if any(
                        s.edition == contest.name
                        and s.problem_index == problem_idx
                        and s.llm == llm
                        and "Failed to get a response from" not in s.whole_answer
                        # and s.answer != "Timeout"
                        # and s.answer != "Failed to get answer."
                        for s in solutions
                    ):
                        logging.info(
                            f"Skipping problem {problem.title} from {contest.name} ({llm.name}), as we already have a solution."
                        )
                        continue

                    # Remove the old answer, if any.
                    solutions = [
                        s
                        for s in solutions
                        if not (
                            s.edition == contest.name
                            and s.problem_index == problem_idx
                            and s.llm == llm
                        )
                    ]

                    statement = problem.to_statement()
                    accepted_format = internal_types.LLMAnswer.accepted_format()

                    question = f"You are tasked with solving a CS/Math problem, which might be in another language.\n"
                    question += f"Here is the problem:\n"
                    question += f"{statement}\n"
                    question += "The accepted format is specified below:\n"
                    question += f"{accepted_format}\n"
                    logging.info(
                        f"Asking {llm.name} a question for problem {problem.title}"
                    )
                    answer = llm_interactor.ask_model(llm, question)
                    result = internal_types.LLMAnswer.from_reply(
                        answer, contest.name, problem_idx, llm
                    )
                    solutions.append(result)
                    logging.info(
                        f"Expected answer: '{problem.correct_answer}', got '{result.answer if result.answer else "no answer"}'"
                    )

                    with open(save_loc, "w") as f:
                        f.write(json.dumps([s.to_json() for s in solutions], indent=2))
                    logger.info(f"Saved solutions to {save_loc}")

        with open(save_loc, "w") as f:
            f.write(json.dumps([s.to_json() for s in solutions], indent=2))
        logger.info(f"Saved solutions to {save_loc}")
