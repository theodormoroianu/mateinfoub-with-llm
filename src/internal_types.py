
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ProblemDificulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

    @classmethod
    def from_romanian(cls, s: str) -> "ProblemDificulty":
        if s == "usor":
            return ProblemDificulty.EASY
        if s == "mediu":
            return ProblemDificulty.MEDIUM
        if s == "greu":
            return ProblemDificulty.HARD
        raise ValueError(f"Invalid difficulty: {s}")

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

    @classmethod
    def from_romanian_json(cls, obj: dict) -> "Problem":
        return Problem(
            title=obj["titlu"],
            markdown_statement=obj["enunt_markdown"],
            answer_variants=list(map(str, obj["variante"])),
            correct_answer=str(obj["raspuns"]),
            difficulty=ProblemDificulty.from_romanian(obj["dificultate"]),
            image_path=obj.get("imagine"),
            image_content=obj.get("continut_imagine"),
        )
    
    @classmethod
    def from_english_json(cls, obj: dict) -> "Problem":
        return Problem(
            title=obj["title"],
            markdown_statement=obj["markdown_statement"],
            answer_variants=list(map(obj["answer_variants"], str)),
            correct_answer=str(obj["correct_answer"]),
            difficulty=ProblemDificulty(obj["difficulty"]),
            image_path=obj.get("image_path"),
            image_content=obj.get("image_content"),
        )
    
    def to_romanian_json(self) -> dict:
        obj = {
            "titlu": self.title,
            "enunt_statement": self.markdown_statement,
            "variante": self.answer_variants,
            "raspuns": self.correct_answer,
            "dificultate": self.difficulty.value,
        }
        if self.image_path is not None:
            obj["imagine"] = self.image_path
        if self.image_content is not None:
            obj["continut_imagine"] = self.image_content
        return obj
    
    def to_english_json(self) -> dict:
        obj = {
            "title": self.title,
            "markdown_statement": self.markdown_statement,
            "answer_variants": self.answer_variants,
            "correct_answer": self.correct_answer,
            "difficulty": self.difficulty.value,
        }
        if self.image_path is not None:
            obj["image_path"] = self.image_path
        if self.image_content is not None:
            obj["image_content"] = self.image_content   
        return obj
    
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

    @classmethod
    def from_romanian_json(cls, obj: dict) -> "Contest":
        return Contest(
            name=obj["name"],
            problems=list(map(Problem.from_romanian_json, obj["probleme"])),
        )
    
    def to_romanian_json(self) -> dict:
        return {
            "name": self.name,
            "probleme": list(map(Problem.to_romanian_json, self.problems)),
        }
    
    @classmethod
    def from_english_json(cls, obj: dict) -> "Contest":
        return Contest(
            name=obj["name"],
            problems=list(map(Problem.from_english_json, obj["problems"])),
        )
    
    def to_english_json(self) -> dict:
        return {
            "name": self.name,
            "problems": list(map(Problem.to_english_json, self.problems)),
        }
