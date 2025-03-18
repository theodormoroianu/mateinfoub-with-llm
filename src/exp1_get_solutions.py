import json
import logging

from tqdm import tqdm

import internal_types
import llm_interactor


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def solve_tasks_asking_llms():
    """
    Asks LLMs to solve the tasks.
    """
    contests = internal_types.Contest.read_all_contests()
    for lang, contests in contests.items():
        logger.info(f"Solving tasks for lang {lang}")
        for contest in contests:
            solutions = []
            logger.info(f"Solving tasks for contest {contest.name}")
            for problem_idx, problem in enumerate(tqdm(contest.problems)):
                logger.info(f"Solving task {problem.title}")
                for llm in llm_interactor.Model._member_map_.values():
                    statement = problem.to_statement()
                    accepted_format = internal_types.LLMAnswer.accepted_format()

                    question = f"You are tasked with solving a CS/Math problem, which might be in another language.\n"
                    question += f"Here is the problem:\n"
                    question += f"{statement}\n"
                    question += "The accepted format is specified below:\n"
                    question += f"{accepted_format}\n"
                    answer = llm_interactor.ask_model(llm, question)
                    result = internal_types.LLMAnswer.from_reply_json(
                        answer, contest.name, problem_idx, llm
                    )
                    solutions.append(result)
                    logging.info(
                        f"Expected answer: '{problem.correct_answer}', got '{result.answer if result.answer else "no answer"}'"
                    )

            save_loc = (
                internal_types.RO_SOLUTIONS_FILE
                if lang == "ro"
                else internal_types.EN_SOLUTIONS_FILE
            )
            with open(save_loc + f"{contest.name}.json", "w") as f:
                f.write(json.dumps([s.to_json() for s in solutions], indent=2))
            logger.info(f"Saved solutions to {save_loc}")
