import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_openai import ChatOpenAI

from .analysis import build_marks_analysis
from .learning_path import build_study_path
from .models import StudentProfile
from .prompts import (
    ANALYSIS_SYSTEM_PROMPT,
    PLANNING_SYSTEM_PROMPT,
    SUMMARY_SYSTEM_PROMPT,
)
from .tools import TOOLS

load_dotenv(dotenv_path=Path(__file__).with_name(".env"))


def _has_provider_credentials(provider: str) -> bool:
    if provider == "openai":
        return bool(os.getenv("OPENAI_API_KEY"))
    if provider == "huggingface":
        return bool(os.getenv("HUGGINGFACEHUB_API_TOKEN"))
    return False


def _create_llm() -> BaseChatModel:
    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()

    if provider == "huggingface":
        endpoint = HuggingFaceEndpoint(
            repo_id=os.getenv("HUGGINGFACE_REPO_ID", "mistralai/Mixtral-8x7B-Instruct-v0.1"),
            task=os.getenv("HUGGINGFACE_TASK", "text-generation"),
            huggingfacehub_api_token=os.getenv("HUGGINGFACEHUB_API_TOKEN"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.2")),
            max_new_tokens=int(os.getenv("HUGGINGFACE_MAX_NEW_TOKENS", "512")),
        )
        return ChatHuggingFace(llm=endpoint)

    if provider == "openai":
        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.2")),
        )

    raise ValueError("Unsupported LLM_PROVIDER. Expected 'openai' or 'huggingface'.")


def _extract_agent_text(result: Any) -> str:
    messages = result.get("messages", []) if isinstance(result, dict) else []
    final_message = messages[-1] if messages else None
    return getattr(final_message, "content", "") if final_message else ""


def _build_local_fallback_analysis(student_data: dict) -> str:
    student = StudentProfile.model_validate(student_data)
    return json.dumps(build_marks_analysis(student), indent=2)


def _build_local_fallback_path(student_data: dict) -> str:
    student = StudentProfile.model_validate(student_data)
    return json.dumps(build_study_path(student), indent=2)


def _build_local_fallback_summary(analysis_json: str, path_json: str) -> str:
    if isinstance(analysis_json, str):
        analysis = json.loads(analysis_json)
    else:
        analysis = analysis_json

    if isinstance(path_json, str):
        path = json.loads(path_json)
    else:
        path = path_json

    weak_subjects = ", ".join(analysis.get("priority_subjects", [])) or "none"
    strong_subjects = ", ".join(analysis.get("top_strengths", [])) or "none"
    weekly_plan = path.get("weekly_plan", {})
    subject_lines = []
    for item in path.get("subject_actions", []):
        actions = item.get("recommended_actions", [])[:2]
        action_text = " ".join(actions) if actions else "Continue steady revision and weekly self-checks."
        subject_lines.append(f"- {item['subject']} ({item['score']}): {action_text}")

    return "\n".join(
        [
            "Student Profile",
            f"- Name: {analysis.get('student', 'unknown')}",
            f"- Grade: {analysis.get('grade', 'unknown')}",
            f"- Goal: {analysis.get('target_goal', 'N/A')}",
            f"- Average score: {analysis.get('average_score', 'N/A')}",
            "",
            "Performance Snapshot",
            f"- Priority subjects: {weak_subjects}",
            f"- Strong subjects: {strong_subjects}",
            "",
            "Weekly Plan",
            f"- Weak subjects: {weekly_plan.get('weak_subjects_hours', 0)} hours",
            f"- Medium subjects: {weekly_plan.get('medium_subjects_hours', 0)} hours",
            f"- Strong subjects: {weekly_plan.get('strong_subjects_hours', 0)} hours",
            "",
            "Subject Guidance",
            *subject_lines,
            "",
            "30-Day Checklist",
            "- Review the weakest topics first",
            "- Practice one short quiz every 3 days",
            "- Track mistakes in a notebook and review them weekly",
            "- Keep one strong subject on light rotation to maintain confidence",
        ]
    )


def create_analysis_agent():
    llm = _create_llm()
    return create_agent(
        model=llm,
        tools=TOOLS,
        system_prompt=ANALYSIS_SYSTEM_PROMPT,
        debug=True,
    )


def create_planning_agent():
    llm = _create_llm()
    return create_agent(
        model=llm,
        tools=TOOLS,
        system_prompt=PLANNING_SYSTEM_PROMPT,
        debug=True,
    )


def create_summary_agent():
    llm = _create_llm()
    return create_agent(
        model=llm,
        tools=[],
        system_prompt=SUMMARY_SYSTEM_PROMPT,
        debug=True,
    )


def run_analysis_agent(student_data: dict) -> str:
    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
    if not _has_provider_credentials(provider):
        return _build_local_fallback_analysis(student_data)

    analysis_agent = create_analysis_agent()
    payload = json.dumps(student_data)
    response = analysis_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Analyze the student profile with the analyze_marks tool and return only the JSON result.\n\n"
                        f"{payload}"
                    ),
                }
            ]
        }
    )
    content = _extract_agent_text(response).strip()
    try:
        json.loads(content)
        return content
    except json.JSONDecodeError:
        return _build_local_fallback_analysis(student_data)


def run_planning_agent(student_data: dict) -> str:
    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
    if not _has_provider_credentials(provider):
        return _build_local_fallback_path(student_data)

    planning_agent = create_planning_agent()
    payload = json.dumps(student_data)
    response = planning_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Generate a learning path with the build_learning_path tool and return only the JSON result.\n\n"
                        f"{payload}"
                    ),
                }
            ]
        }
    )
    content = _extract_agent_text(response).strip()
    try:
        json.loads(content)
        return content
    except json.JSONDecodeError:
        return _build_local_fallback_path(student_data)


def run_summary_agent(analysis_json: str, path_json: str) -> str:
    try:
        analysis = json.loads(analysis_json)
        path = json.loads(path_json)
    except json.JSONDecodeError:
        return _build_local_fallback_summary(analysis_json, path_json)

    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
    if not _has_provider_credentials(provider):
        return _build_local_fallback_summary(analysis, path)

    summary_agent = create_summary_agent()
    response = summary_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Use the following student performance analysis and study path to write a motivating summary.\n\n"
                        f"ANALYSIS:\n{analysis_json}\n\nLEARNING PATH:\n{path_json}"
                    ),
                }
            ]
        }
    )
    return _extract_agent_text(response).strip() or _build_local_fallback_summary(analysis_json, path_json)
