import json
import os
from pathlib import Path
from typing import Any
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import ToolMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from .prompts import PLANNER_SYSTEM_PROMPT, EXECUTOR_SYSTEM_PROMPT, CRITIC_SYSTEM_PROMPT, SUMMARY_SYSTEM_PROMPT
from .tools import MCP_TOOLS

load_dotenv(dotenv_path=Path(__file__).with_name(".env"))

def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    return default if value is None else value.strip().lower() in {"1", "true", "yes", "on"}

def _create_llm(*, json_mode: bool = False) -> BaseChatModel:
    endpoint = HuggingFaceEndpoint(
        repo_id=os.getenv("HUGGINGFACE_REPO_ID", "Qwen/Qwen3.5-9B"),
        task=os.getenv("HUGGINGFACE_TASK", "text-generation"),
        huggingfacehub_api_token=os.getenv("HUGGINGFACEHUB_API_TOKEN"),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.2")),
        max_new_tokens=int(os.getenv("HUGGINGFACE_MAX_NEW_TOKENS", "1024")),
    )
    kwargs: dict[str, Any] = {"extra_body": {"chat_template_kwargs": {"enable_thinking": _env_bool("QWEN_ENABLE_THINKING", False)}}}
    if json_mode: kwargs["response_format"] = {"type": "json_object"}
    return ChatHuggingFace(llm=endpoint, model_kwargs=kwargs)

def _require_token() -> None:
    if not os.getenv("HUGGINGFACEHUB_API_TOKEN"):
        raise RuntimeError("HUGGINGFACEHUB_API_TOKEN is not configured; fallback is disabled")

def _extract_text(result: Any) -> str:
    messages = result.get("messages", []) if isinstance(result, dict) else []
    message = messages[-1] if messages else None
    content = getattr(message, "content", "") if message else ""
    if not content:
        raise ValueError(f"Agent returned empty content; response metadata: {getattr(message, 'response_metadata', {})}")
    return content

def _validate_json(content: str, required: set[str]) -> str:
    content = content.strip()
    start, end = content.find("{"), content.rfind("}")
    if start < 0 or end < start: raise ValueError(f"Agent response contains no JSON object: {content[:200]!r}")
    try: parsed = json.loads(content[start:end + 1])
    except json.JSONDecodeError as exc: raise ValueError(f"Agent returned invalid JSON: {exc}") from exc
    missing = required.difference(parsed)
    if missing: raise ValueError(f"Agent response missing keys: {sorted(missing)}")
    return json.dumps(parsed, indent=2)

def _executor_result(result: Any) -> str:
    results: dict[str, str] = {}
    trace: list[str] = []
    for message in result.get("messages", []):
        if isinstance(message, ToolMessage):
            content = message.content if isinstance(message.content, str) else json.dumps(message.content)
            results[message.name or ""] = content
            trace.append(message.name or "")
    analysis = results.get("mcp_analyze_marks")
    path = results.get("mcp_refine_learning_path") or results.get("mcp_build_learning_path")
    if analysis is None or path is None: raise ValueError("Executor did not call the required MCP tools")
    json.loads(analysis); json.loads(path)
    return json.dumps({"analysis_json": analysis, "learning_path_json": path, "tool_trace": trace, "execution_notes": "Packaged directly from MCP ToolMessage results."}, indent=2)

def _critic_evidence(executor_json: str) -> dict[str, Any]:
    executor = json.loads(executor_json); analysis = json.loads(executor["analysis_json"]); path = json.loads(executor["learning_path_json"])
    terms = ("visual", "diagram", "map", "practice", "quiz", "test", "flashcard")
    style = [a for s in path.get("subject_actions", []) for a in s.get("recommended_actions", []) if any(t in a.lower() for t in terms)][:3]
    return {"tool_trace": executor.get("tool_trace", []), "analysis": {k: analysis.get(k, []) for k in ("average_score", "priority_subjects", "top_strengths", "subjects")}, "learning_path": {"weekly_plan": path.get("weekly_plan", {}), "phase_names": [p.get("phase") for p in path.get("phases", [])], "learning_style_evidence": style, "revision": path.get("revision"), "critic_directives": path.get("critic_directives", [])}}

def _summary_evidence(analysis_json: str, path_json: str, critic_json: str) -> dict[str, Any]:
    analysis, path, critic = json.loads(analysis_json), json.loads(path_json), json.loads(critic_json)
    return {"performance": {k: analysis.get(k, []) for k in ("average_score", "priority_subjects", "top_strengths")}, "weekly_plan": path.get("weekly_plan", {}), "critic": {k: critic.get(k, []) for k in ("verdict", "recommended_adjustments", "coaching_notes")}}

def create_planner_agent(): return create_agent(model=_create_llm(json_mode=True), tools=[], system_prompt=PLANNER_SYSTEM_PROMPT)
def create_executor_agent(): return create_agent(model=_create_llm(), tools=MCP_TOOLS, system_prompt=EXECUTOR_SYSTEM_PROMPT)
def create_critic_agent(): return create_agent(model=_create_llm(json_mode=True), tools=[], system_prompt=CRITIC_SYSTEM_PROMPT)
def create_summary_agent(): return create_agent(model=_create_llm(), tools=[], system_prompt=SUMMARY_SYSTEM_PROMPT)

def run_planner_agent(student: dict, critic_json: str | None = None) -> str:
    _require_token()
    try:
        result = create_planner_agent().invoke({"messages": [{"role": "user", "content": f"Plan executor work.\nSTUDENT:{json.dumps(student)}\nCRITIC_FEEDBACK:{critic_json or '{}'}"}]})
        return _validate_json(_extract_text(result), {"objective", "required_mcp_tools", "execution_steps", "success_criteria"})
    except Exception as exc: raise RuntimeError(f"Qwen planner agent failed: {exc}") from exc

def run_executor_agent(student: dict, planner_json: str, critic_json: str | None = None, path_json: str | None = None) -> str:
    _require_token()
    try:
        prompt = f"Execute using MCP tools; then say DONE.\nSTUDENT:{json.dumps(student)}\nPLANNER:{planner_json}\nPRIOR_CRITIC:{critic_json or '{}'}\nPRIOR_LEARNING_PATH:{path_json or '{}'}"
        return _executor_result(create_executor_agent().invoke({"messages": [{"role": "user", "content": prompt}]}))
    except Exception as exc: raise RuntimeError(f"Qwen executor agent failed: {exc}") from exc

def run_critic_agent(student: dict, planner_json: str, executor_json: str, revision_count: int) -> str:
    _require_token()
    try:
        evidence = json.dumps(_critic_evidence(executor_json), separators=(",", ":"))
        prompt = f"Return validation JSON.\nSTUDENT:{json.dumps(student)}\nPLANNER:{planner_json}\nEXECUTOR_EVIDENCE:{evidence}\nREVISION_COUNT:{revision_count}"
        return _validate_json(_extract_text(create_critic_agent().invoke({"messages": [{"role": "user", "content": prompt}]})), {"approved", "alignment_score", "verdict", "feedback_to_planner", "feedback_to_executor"})
    except Exception as exc: raise RuntimeError(f"Qwen critic agent failed: {exc}") from exc

def run_summary_agent(student: dict, analysis_json: str, path_json: str, critic_json: str) -> str:
    _require_token()
    try:
        evidence = json.dumps(_summary_evidence(analysis_json, path_json, critic_json), separators=(",", ":"))
        return _extract_text(create_summary_agent().invoke({"messages": [{"role": "user", "content": f"Write final report.\nSTUDENT:{json.dumps(student)}\nEVIDENCE:{evidence}"}]})).strip()
    except Exception as exc: raise RuntimeError(f"Qwen summary agent failed: {exc}") from exc
