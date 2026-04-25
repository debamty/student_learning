import json
from typing import TypedDict

from langgraph.graph import StateGraph

from .agent import run_review_agent, run_summary_agent
from .analysis import build_marks_analysis
from .learning_path import build_study_path
from .models import StudentProfile


class StudentInput(TypedDict):
    student_json: str


class StudentGraphState(TypedDict, total=False):
    student_json: str
    analysis_json: str
    learning_path_json: str
    review_json: str
    final_report: str


class GraphContext(TypedDict, total=False):
    pass


def _analysis_node(state: StudentGraphState, runtime: object) -> StudentGraphState:
    student = StudentProfile.model_validate_json(state["student_json"])
    return {"analysis_json": json.dumps(build_marks_analysis(student), indent=2)}


def _planning_node(state: StudentGraphState, runtime: object) -> StudentGraphState:
    student = StudentProfile.model_validate_json(state["student_json"])
    return {"learning_path_json": json.dumps(build_study_path(student), indent=2)}


def _review_node(state: StudentGraphState, runtime: object) -> StudentGraphState:
    student_data = json.loads(state["student_json"])
    return {
        "review_json": run_review_agent(
            student_data,
            state["analysis_json"],
            state["learning_path_json"],
        )
    }


def _summary_node(state: StudentGraphState, runtime: object) -> StudentGraphState:
    student_data = json.loads(state["student_json"])
    return {
        "final_report": run_summary_agent(
            student_data,
            state["analysis_json"],
            state["learning_path_json"],
            state["review_json"],
        )
    }


def build_student_graph() -> object:
    graph = StateGraph(
        state_schema=StudentGraphState,
        context_schema=GraphContext,
        input_schema=StudentInput,
        output_schema=StudentGraphState,
    )

    graph.add_node("analysis", _analysis_node)
    graph.add_node("planning", _planning_node)
    graph.add_node("review", _review_node)
    graph.add_node("summary", _summary_node)

    graph.add_edge("analysis", "planning")
    graph.add_edge("planning", "review")
    graph.add_edge("review", "summary")

    graph.set_entry_point("analysis")
    graph.set_finish_point("summary")

    return graph.compile()
