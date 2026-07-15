import json
from mcp.server.fastmcp import FastMCP
from .analysis import build_marks_analysis
from .learning_path import build_study_path
from .models import StudentProfile

mcp = FastMCP("student-study-tools", host="127.0.0.1", port=8001)

@mcp.tool()
def analyze_marks(student_json: str) -> str:
    return json.dumps(build_marks_analysis(StudentProfile.model_validate_json(student_json)), indent=2)

@mcp.tool()
def build_learning_path(student_json: str) -> str:
    return json.dumps(build_study_path(StudentProfile.model_validate_json(student_json)), indent=2)

@mcp.tool()
def refine_learning_path(student_json: str, path_json: str, critic_json: str) -> str:
    student = StudentProfile.model_validate_json(student_json)
    refined, critic = dict(json.loads(path_json)), json.loads(critic_json)
    feedback = critic.get("feedback_to_executor") or critic.get("recommended_adjustments", [])
    if isinstance(feedback, str): feedback = [feedback]
    refined["revision"] = {"source": "critic_feedback", "applied_adjustments": feedback[:5]}
    weak = [name for name, score in student.marks.items() if score < 60]
    if weak: refined["critic_directives"] = [f"Prioritize {', '.join(weak)}.", "Review mistakes weekly."]
    return json.dumps(refined, indent=2)

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
