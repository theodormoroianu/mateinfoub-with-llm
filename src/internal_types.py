from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional
import json
import logging
import pathlib

import llm_interactor
import script_runner

logger = logging.getLogger(__name__)

# Directory where our statements and results are stored.
DATA_DIR = pathlib.Path(__file__).parent.parent / "data" / "statements"

# Original statements.
RO_STATEMENTS_FILE = DATA_DIR / "contests_ro.json"

# Translated statements.
EN_STATEMENTS_FILE = DATA_DIR / "contests_en.json"

# Solutions in Romanian.
RO_SOLUTIONS_FILE = DATA_DIR / "solutions_ro.json"

# Solutions in English.
EN_SOLUTIONS_FILE = DATA_DIR / "solutions_en.json"


class ProblemDificulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass
class Problem:
    """
    Stores a problem instance.
    """

    title: str
    markdown_statement: str
    answer_variants: list[str]
    correct_answer: str
    difficulty: ProblemDificulty
    image_path: Optional[str]
    image_content: Optional[str]

    @staticmethod
    def from_json(obj: dict) -> "Problem":
        return Problem(
            title=obj["title"],
            markdown_statement=obj["markdown_statement"],
            answer_variants=obj["answer_variants"],
            correct_answer=obj["correct_answer"],
            difficulty=ProblemDificulty(obj["difficulty"]),
            image_path=obj.get("image_path"),
            image_content=(
                obj.get("image_content") if obj.get("image_content") else None
            ),
        )

    def to_json(self) -> dict:
        result = asdict(self)
        if self.image_content is None:
            result.pop("image_content")
        return result

    def image_url(self) -> Optional[str]:
        """
        If the problem has an image, returns the URL to the image.
        """
        if self.image_path is None:
            return None
        return f"https://mateinfo-ub.github.io/{self.image_path}"

    def to_statement(self) -> str:
        """
        Converts the problem to a statement, which can be passed to the LLM.
        """
        statement = self.markdown_statement
        if self.image_content:
            statement += f"\nContent of the image:\n{self.image_content}"

        statement += "\n\nAnswer variants:\n"
        for idx, variant in enumerate(self.answer_variants):
            statement += f" * {variant}\n"
        return statement


@dataclass
class Contest:
    """
    Stores a contest instance.
    """

    name: str
    problems: list[Problem]

    @staticmethod
    def from_json(obj: dict) -> "Contest":
        return Contest(
            name=obj["name"],
            problems=[Problem.from_json(p) for p in obj["problems"]],
        )

    def to_json(self) -> dict:
        return asdict(self)

    @staticmethod
    def read_all_contests() -> dict[str, list["Contest"]]:
        """
        Reads all contests from a file.
        """
        with open(EN_STATEMENTS_FILE, "r") as f:
            en_content = json.loads(f.read())
            en_content = [Contest.from_json(c) for c in en_content]
        with open(RO_STATEMENTS_FILE, "r") as f:
            ro_content = json.loads(f.read())
            ro_content = [Contest.from_json(c) for c in ro_content]
        return {"en": en_content, "ro": ro_content}


@dataclass
class LLMAnswer:
    """
    An LLM's solution. Can either be a python script or a punctual answer.
    """

    # Explanation of the model's reasoning.
    reasoning: str

    # If present, the python code we have to run to get the answer.
    python_code: Optional[str]

    # If present, the answer outputed by the model.
    answer: str

    # The edition name
    edition: str

    # The problem's index
    problem_index: int

    # The LLM used to generate the answer
    llm: llm_interactor.Model

    @staticmethod
    def accepted_format() -> str:
        """
        Returns a string which describes the accepted format of the answer.
        """
        answer = "You have to output the correct answer (not the index, the actual value of the answer).\n"
        answer += "The answer is computed with a diff check, so it has to be EXACTLY the right answer.\n"
        answer += "You can answer in 2 ways: by providing the answer (i.e. the string), or by providing a Python3.12 script which, when ran with a timeout of ~10 seconds, outputs EXACTLY the right answer.\n"
        answer += """Please reply in the following format, with separator blocks, in the following format:
If you want to provide the answer using a Python script:
<REASONING>
[your reasoning steps here]
</REASONING>
<PYTHON CODE>
[your python code here]
</PYTHON CODE>

OR (if you want to provide the answer directly):
<REASONING>
[your reasoning steps here]
</REASONING>
<ANSWER>
[your answer here]
</ANSWER>
"""
        answer += "NEVER include both <PYTHON CODE> and <ANSWER> blocks in the same message. ONLY include one or the other."
        return answer

    @staticmethod
    def from_reply(
        content: str, edition: str, problem_index: int, llm: llm_interactor.Model
    ) -> Optional["LLMAnswer"]:
        """
        Tries to parse the answer, returns None if the answer
        is not in the right format.
        """
        logger.info(
            f"Trying to parse the answer for {edition} problem {problem_index} ({llm})..."
        )

        try:
            # We expect to have something like this:
            # <START REASONING>
            # [reasoning]
            # <END REASONING>
            # <START PYTHON CODE> OR <START ANSWER>
            # [python code]
            # <END PYTHON CODE> OR <END ANSWER>
            assert "<REASONING>" in content, "No <REASONING> found."
            assert "</REASONING>" in content, "No </REASONING> found."
            reasoning = content.split("<REASONING>")[1].split("</REASONING>")[0]

            if "<PYTHON CODE>" in content:
                assert "</PYTHON CODE>" in content, "No <PYTHON CODE> found."
                if "<ANSWER>" in content:
                    logger.error("Both <PYTHON CODE> and <ANSWER> found.")
                python_code = content.split("<PYTHON CODE>")[1].split("</PYTHON CODE>")[
                    0
                ]
                answer = script_runner.run_script(python_code).strip()
            else:
                assert "<ANSWER>" in content, "No <ANSWER> or <PYTHON CODE> found."
                assert "</ANSWER>" in content, "No </ANSWER> found."
                python_code = None
                answer = content.split("<ANSWER>")[1].split("</ANSWER>")[0].strip()

            llm_answer = LLMAnswer(
                reasoning=reasoning,
                python_code=python_code,
                answer=answer,
                edition=edition,
                problem_index=problem_index,
                llm=llm,
            )
            return llm_answer
        except Exception as e:
            logger.warning(f"Failed to get answer: {e}")
            logger.warning(f"Content: {content}")
            return LLMAnswer(
                reasoning="Failed to get answer.",
                python_code=None,
                answer="Failed to get answer.",
                edition=edition,
                problem_index=problem_index,
                llm=llm,
            )

    @staticmethod
    def from_json(obj: dict) -> "LLMAnswer":
        return LLMAnswer(
            reasoning=obj["reasoning"],
            python_code=obj.get("python_code"),
            answer=obj.get("answer"),
            edition=obj["edition"],
            problem_index=obj["problem_index"],
            llm=llm_interactor.Model(obj["llm"]),
        )

    def to_json(self) -> dict:
        return asdict(self)
