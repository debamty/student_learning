import json

from . import run_student_learning_agent
from .sample_data import SAMPLE_STUDENTS


def _build_structured_report(student_data: dict, result: dict) -> dict:
    raw = result.get("raw", {})

    if raw.get("mode") == "local-fallback":
        analysis = raw["analysis"]
        learning_path = raw["learning_path"]
        return {
            "student": analysis["student"],
            "grade": analysis["grade"],
            "goal": analysis["target_goal"],
            "average_score": analysis["average_score"],
            "weak_subjects": analysis["priority_subjects"],
            "strong_subjects": analysis["top_strengths"],
            "weekly_plan": learning_path["weekly_plan"],
            "phases": learning_path["phases"],
            "subject_actions": learning_path["subject_actions"],
        }

    return {
        "student": student_data["name"],
        "grade": student_data["grade"],
        "goal": student_data["target_goal"],
        "llm_output": result["output"],
    }


def main() -> None:
    reports = []

    for student in SAMPLE_STUDENTS:
        result = run_student_learning_agent(student)
        reports.append(_build_structured_report(student, result))

    print(json.dumps({"students": reports}, indent=2))
