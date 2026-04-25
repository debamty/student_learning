import json
from typing_extensions import Annotated, TypedDict

from langgraph.graph import StateGraph

from .agent import run_analysis_agent, run_planning_agent, run_summary_agent


class StudentInput(TypedDict):
    student_json: str


class StudentGraphState(TypedDict, total=False):
    student_json: str
    analysis_json: str
    learning_path_json: str
    final_report: str


class GraphContext(TypedDict, total=False):
    pass


def _analyze_node(state: StudentGraphState, runtime: object) -> StudentGraphState:
    student_json = state["student_json"]
    return {"analysis_json": run_analysis_agent(json.loads(student_json))}


def _planning_node(state: StudentGraphState, runtime: object) -> StudentGraphState:
    student_json = state["student_json"]
    return {"learning_path_json": run_planning_agent(json.loads(student_json))}


def _summary_node(state: StudentGraphState, runtime: object) -> StudentGraphState:
    return {
        "final_report": run_summary_agent(
            state["analysis_json"],
            state["learning_path_json"],
        )
    }


def build_student_graph() -> object:
    graph = StateGraph(
        state_schema=StudentGraphState,
        context_schema=GraphContext,
        input_schema=StudentInput,
        output_schema=StudentGraphState,
    )

    graph.add_node("analysis", _analyze_node)
    graph.add_node("planning", _planning_node)
    graph.add_node("summary", _summary_node)

    graph.add_edge("analysis", "planning")
    graph.add_edge("planning", "summary")

    graph.set_entry_point("analysis")
    graph.set_finish_point("summary")

    return graph.compile()
