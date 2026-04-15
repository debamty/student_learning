import json

from langchain_core.tools import tool

from .analysis import build_marks_analysis
from .learning_path import build_study_path
from .models import StudentProfile


@tool
def analyze_marks(student_json: str) -> str:
    """Analyze student marks and identify strengths, weak subjects, and urgency."""
    student = StudentProfile.model_validate_json(student_json)
    return json.dumps(build_marks_analysis(student), indent=2)


@tool
def build_learning_path(student_json: str) -> str:
    """Generate a structured study path customized to marks, goal, and available weekly hours."""
    student = StudentProfile.model_validate_json(student_json)
    return json.dumps(build_study_path(student), indent=2)


TOOLS = [analyze_marks, build_learning_path]
