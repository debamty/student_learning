import json

from .graph import build_student_graph
from .sample_data import SAMPLE_STUDENTS


def _build_structured_report(student_data: dict, graph_output: dict) -> dict:
    return {
        "student": student_data["name"],
        "grade": student_data["grade"],
        "goal": student_data["target_goal"],
        "final_report": graph_output.get("final_report", ""),
        "analysis_json": graph_output.get("analysis_json", ""),
        "learning_path_json": graph_output.get("learning_path_json", ""),
        "review_json": graph_output.get("review_json", ""),
    }


def run_student_learningpath_langgraph(student_data: dict) -> dict:
    graph = build_student_graph()
    output = graph.invoke({"student_json": json.dumps(student_data)})
    return {"final_report": output.get("final_report", ""), "raw": output}


def main() -> None:
    graph = build_student_graph()
    reports = []

    for student in SAMPLE_STUDENTS:
        output = graph.invoke({"student_json": json.dumps(student)})
        reports.append(_build_structured_report(student, output))

    print(json.dumps({"students": reports}, indent=2))
