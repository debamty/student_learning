import json
from typing import Literal, TypedDict
from langgraph.graph import StateGraph
from .agent import run_planner_agent, run_executor_agent, run_critic_agent, run_summary_agent

class StudentInput(TypedDict): student_json: str
class StudentGraphState(TypedDict, total=False):
    student_json: str; planner_json: str; executor_json: str; analysis_json: str
    learning_path_json: str; critic_json: str; revision_count: int; final_report: str
class GraphContext(TypedDict, total=False): pass

def _planner_node(state, runtime): return {"planner_json": run_planner_agent(json.loads(state["student_json"]), state.get("critic_json"))}
def _executor_node(state, runtime):
    result = run_executor_agent(json.loads(state["student_json"]), state["planner_json"], state.get("critic_json"), state.get("learning_path_json"))
    parsed = json.loads(result)
    return {"executor_json": result, "analysis_json": parsed["analysis_json"], "learning_path_json": parsed["learning_path_json"]}
def _critic_node(state, runtime): return {"critic_json": run_critic_agent(json.loads(state["student_json"]), state["planner_json"], state["executor_json"], state.get("revision_count", 0))}
def _revision_node(state, runtime): return {"revision_count": state.get("revision_count", 0) + 1}
def _summary_node(state, runtime): return {"final_report": run_summary_agent(json.loads(state["student_json"]), state["analysis_json"], state["learning_path_json"], state["critic_json"])}
def _route(state) -> Literal["revise", "summary"]:
    return "summary" if json.loads(state["critic_json"]).get("approved") or state.get("revision_count", 0) >= 1 else "revise"

def build_student_graph():
    graph = StateGraph(state_schema=StudentGraphState, context_schema=GraphContext, input_schema=StudentInput, output_schema=StudentGraphState)
    for name, node in (("planner", _planner_node), ("executor", _executor_node), ("critic", _critic_node), ("revision", _revision_node), ("summary", _summary_node)): graph.add_node(name, node)
    graph.add_edge("planner", "executor"); graph.add_edge("executor", "critic")
    graph.add_conditional_edges("critic", _route, {"revise": "revision", "summary": "summary"})
    graph.add_edge("revision", "planner"); graph.set_entry_point("planner"); graph.set_finish_point("summary")
    return graph.compile()
