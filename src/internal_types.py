from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional
import json
import logging
import pathlib
import dirtyjson

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
        # fmt = {
        #     "reasoning": "The techniques you used for solving the problem, concise, mandatory",
        #     "python_code": "If you choose to solve the problem using a python script, the python3.12 script, without dependencies on 3rd party libs, which has to print EXACTLY the right answer to stdout (only the right answer, nothing more). The field doesn't exist if you reply with an answer.",
        #     "answer": "If you choose to solve the problem directly, this is the correct answer. The field doesn't exist if you reply with a script. The answer is the actual result, not the letter / index of the answer.",
        # }
        answer = "You have to output the correct answer (not the index, the actual value of the answer).\n"
        answer += "The answer is computed with a diff check, so it has to be EXACTLY the right answer.\n"
        answer += "You can answer in 2 ways: by providing the answer (i.e. the string), or by providing a Python3.12 script which, when ran with a timeout of ~10 seconds, outputs EXACTLY the right answer.\n"
        answer += "Please reply with a valid JSON, in the following format, without any additional notes or comments:\n"
        answer += """Use this JSON schema:

Answer = {'reasoning': str, 'answer': optional[str], 'python_code': optional[str]}
Return: Answer
"""
        answer += "For instance, your output could be this:\n"
        answer += '{"reasoning": "I used the following techniques to solve the problem\\n", "answer": "42"}\n'
        answer += "or\n"
        answer += '{"reasoning": "I used the following techniques to solve the problem:\\n", "python_code": "print(\'42\')"}\n'
        answer += "\nThe reasoning field is mandatory, and MUST NOT contain any LaTeX, quotes, formulas with dollar signs, or special characters. The python code MUST NOT contain double quotes, use single quotes instead.\n"
        # answer += "Your answer needs to be a valid JSON, so make sure to ESCAPE ALL THE DOUBLE QUOTES within the JSON.\n"
        # answer += "AGAIN, ESCAPE ALL DOUBLE QUOTES!!!"
        return answer

    @staticmethod
    def from_reply_json(
        content: str, edition: str, problem_index: int, llm: llm_interactor.Model
    ) -> Optional["LLMAnswer"]:
        """
        Tries to parse the answer, returns None if the answer
        is not in the right format.
        """
        logger.info(
            f"Trying to parse the answer for {edition} problem {problem_index} ({llm})..."
        )
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.replace("\\(", "(").replace("\\)", ")")
        content = content.replace("\\[", "[").replace("\\]", "]")
        content = content.replace("\\{", "{").replace("\\}", "}")

        logger.debug(f"Content: {content}")
        try:
            # obj = json.loads(content, strict=False)
            obj = dirtyjson.loads(content)
            reasoning = obj["reasoning"]
            if "answer" in obj:
                answer = obj["answer"]
                python_code = None
            if "python_code" in obj:
                python_code = obj["python_code"]
                answer = script_runner.run_script(python_code)
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
