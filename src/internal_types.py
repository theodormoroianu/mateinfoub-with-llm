from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional
import json
import logging
import pathlib

import script_runner

# Directory where our statements and results are stored.
DATA_DIR = pathlib.Path(__file__).parent.parent / "data" / "statements"

# Original statements.
RO_STATEMENTS_FILE = DATA_DIR / "ro.json"

# Translated statements.
EN_STATEMENTS_FILE = DATA_DIR / "en.json"


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


@dataclass
class LLMAnswer:
    """
    An LLM's solution. Can either be a python script or a punctual answer.
    """

    # Explanation of the model's reasoning.
    reasoning: str

    # If present, the python code we have to run to get the answer.
    python_code: Optional[str]

    # The output of the python code, if present.
    python_code_output: Optional[str]

    # If present, the answer outputed by the model.
    answer: str

    @staticmethod
    def accepted_format() -> str:
        """
        Returns a string which describes the accepted format of the answer.
        """
        fmt = {
            "reasoning": "The techniques you used for solving the problem, concise, mandatory",
            "python_code": "If you choose to solve the problem using a python script, the python3.12 script, without dependencies on 3rd party libs, which has to print EXACTLY the right answer to stdout (only the right answer, nothing more). The field doesn't exist if you reply with an answer.",
            "answer": "If you choose to solve the problem directly, this is the correct answer. The field doesn't exist if you reply with a script.",
        }
        answer = "You have to output the correct answer (not the index, the actual value of the answer).\n"
        answer += "The answer is computed with a diff check, so it has to be EXACTLY the right answer.\n"
        answer += "You can answer in 2 ways: by providing the answer (i.e. the string), or by providing a Python3.12 script which, when ran with a timeout of ~10 seconds, outputs EXACTLY the right answer.\n"
        answer += "Please reply with a valid JSON, in the following format, without any additional notes:\n"
        answer += json.dumps(fmt)
        return answer

    @staticmethod
    def from_reply_json(content: str) -> Optional["LLMAnswer"]:
        """
        Tries to parse the answer, returns None if the answer
        is not in the right format.
        """
        try:
            obj = json.loads(content)
            llm_answer = LLMAnswer()
            llm_answer.reasoning = obj["reasoning"]
            if "answer" in obj:
                llm_answer.answer = obj["answer"]
            if "python_code" in obj:
                llm_answer.python_code = obj["python_code"]
                llm_answer.python_code_output = script_runner.run_script(
                    llm_answer.python_code
                )
            return llm_answer
        except Exception as e:
            logging.warning(f"Failed to parse json: {e}")
            return None

    @staticmethod
    def from_json(obj: dict) -> "LLMAnswer":
        return LLMAnswer(**obj)

    def to_json(self) -> dict:
        return asdict(self)
