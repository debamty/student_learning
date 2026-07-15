import json
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from .agent import run_planner_agent, run_executor_agent, run_critic_agent, run_summary_agent
from .graph import build_student_graph
from .models import StudentProfile

app = FastAPI(title="Student Learning Multi-Agent POC", version="2.0.0")
logger = logging.getLogger(__name__)

def _chain(exc):
    result, seen = [], set()
    while exc is not None and id(exc) not in seen:
        seen.add(id(exc)); result.append({"type": type(exc).__name__, "message": str(exc)}); exc = exc.__cause__ or exc.__context__
    return result

@app.exception_handler(Exception)
async def errors(request: Request, exc: Exception):
    logger.exception("Request failed")
    chain = _chain(exc)
    return JSONResponse(status_code=500, content={"status": "error", "endpoint": request.url.path, "error": chain[0], "causes": chain[1:], "fallback_used": False})

class PlannerRequest(BaseModel): student: StudentProfile; critic_json: str | None = None
class ExecutorRequest(BaseModel): student: StudentProfile; planner_json: str; critic_json: str | None = None; learning_path_json: str | None = None
class CriticRequest(BaseModel): student: StudentProfile; planner_json: str; executor_json: str; revision_count: int = 0
class SummaryRequest(BaseModel): student: StudentProfile; analysis_json: str; learning_path_json: str; critic_json: str

@app.get("/health")
def health(): return {"status": "ok"}
@app.post("/agents/planner")
def planner(r: PlannerRequest): return {"agent": "planner", "result": json.loads(run_planner_agent(r.student.model_dump(), r.critic_json))}
@app.post("/agents/executor")
def executor(r: ExecutorRequest): return {"agent": "executor", "result": json.loads(run_executor_agent(r.student.model_dump(), r.planner_json, r.critic_json, r.learning_path_json))}
@app.post("/agents/critic")
def critic(r: CriticRequest): return {"agent": "critic", "result": json.loads(run_critic_agent(r.student.model_dump(), r.planner_json, r.executor_json, r.revision_count))}
@app.post("/agents/summary")
def summary(r: SummaryRequest): return {"agent": "summary", "result": run_summary_agent(r.student.model_dump(), r.analysis_json, r.learning_path_json, r.critic_json)}

def _pretty(student, output):
    executor = json.loads(output["executor_json"])
    return {"student": student.model_dump(), "planner": json.loads(output["planner_json"]), "execution": {"tool_trace": executor.get("tool_trace", []), "notes": executor.get("execution_notes", ""), "analysis": json.loads(output["analysis_json"]), "learning_path": json.loads(output["learning_path_json"])}, "critic": json.loads(output["critic_json"]), "revision_count": output.get("revision_count", 0), "final_report": output.get("final_report", "")}

@app.post("/workflow")
def workflow(student: StudentProfile):
    return _pretty(student, build_student_graph().invoke({"student_json": student.model_dump_json()}))
