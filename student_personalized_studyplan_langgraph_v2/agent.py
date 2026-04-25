import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_openai import ChatOpenAI

from .models import StudentProfile
from .prompts import REVIEW_SYSTEM_PROMPT, SUMMARY_SYSTEM_PROMPT

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
            repo_id=os.getenv("HUGGINGFACE_REPO_ID", "meta-llama/Llama-3.1-8B-Instruct:cerebras"),
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


def _build_local_review(student_data: dict, analysis_json: str, path_json: str) -> str:
    student = StudentProfile.model_validate(student_data)
    analysis = json.loads(analysis_json)
    path = json.loads(path_json)

    weekly_plan = path.get("weekly_plan", {})
    weak_hours = weekly_plan.get("weak_subjects_hours", 0)
    medium_hours = weekly_plan.get("medium_subjects_hours", 0)
    strong_hours = weekly_plan.get("strong_subjects_hours", 0)
    priority_subjects = analysis.get("priority_subjects", [])
    top_strengths = analysis.get("top_strengths", [])

    risks = []
    adjustments = []

    if priority_subjects and weak_hours == 0:
        risks.append("No weekly hours are reserved for weak subjects.")
        adjustments.append("Reserve weekly time for the weakest subjects before adding extra revision elsewhere.")

    if student.weekly_study_hours <= 6 and len(priority_subjects) >= 2:
        risks.append("Study hours are limited compared with the number of weak subjects.")
        adjustments.append("Focus on the top one or two weak subjects first instead of trying to improve everything at once.")

    if "visual" in student.preferred_style.lower():
        adjustments.append("Use diagrams, color-coded notes, and chapter maps to match the student's visual learning preference.")

    if "practice" in student.preferred_style.lower():
        adjustments.append("Add short timed practice blocks each week so revision turns into score improvement.")

    verdict = "well_aligned" if not risks else "needs_refinement"
    alignment_score = 9 if not risks else max(6, 9 - len(risks))

    review = {
        "alignment_score": alignment_score,
        "verdict": verdict,
        "strengths": [
            f"The plan gives explicit attention to weak subjects such as {', '.join(priority_subjects) or 'none'}.",
            f"It also preserves stronger subjects such as {', '.join(top_strengths) or 'none'} through lighter maintenance.",
            f"The weekly hour split is weak={weak_hours}, medium={medium_hours}, strong={strong_hours}.",
        ],
        "risks": risks or ["No major alignment issues were detected in the deterministic plan."],
        "recommended_adjustments": adjustments[:4] or ["Keep the current plan and review progress at the end of each week."],
        "coaching_notes": [
            "Track mistakes weekly and use them to choose the next revision topics.",
            "Keep the study load realistic so consistency stays high over the month.",
        ],
    }
    return json.dumps(review, indent=2)


def _build_local_summary(student_data: dict, analysis_json: str, path_json: str, review_json: str) -> str:
    student = StudentProfile.model_validate(student_data)
    analysis = json.loads(analysis_json)
    path = json.loads(path_json)
    review = json.loads(review_json)

    weak_subjects = ", ".join(analysis.get("priority_subjects", [])) or "none"
    strong_subjects = ", ".join(analysis.get("top_strengths", [])) or "none"
    weekly_plan = path.get("weekly_plan", {})
    adjustments = review.get("recommended_adjustments", [])

    lines = [
        f"{student.name} is currently working toward {student.target_goal} with an average score of {analysis.get('average_score', 'N/A')}.",
        f"The biggest improvement opportunities are {weak_subjects}, while the current strengths are {strong_subjects}.",
        "",
        "Suggested weekly routine:",
        f"- Weak subjects: {weekly_plan.get('weak_subjects_hours', 0)} hours",
        f"- Medium subjects: {weekly_plan.get('medium_subjects_hours', 0)} hours",
        f"- Strong subjects: {weekly_plan.get('strong_subjects_hours', 0)} hours",
        "",
        "Reviewer suggestions:",
    ]

    lines.extend(f"- {item}" for item in adjustments[:4])
    lines.extend(
        [
            "",
            "30-day checklist:",
            "- Rebuild the weakest topics first and track common mistakes.",
            "- Take one short quiz every 3 to 4 days.",
            "- Review progress weekly and adjust focus if one subject is still stuck.",
            "- Keep one stronger subject in rotation to maintain confidence.",
        ]
    )
    return "\n".join(lines)


def create_review_agent():
    llm = _create_llm()
    return create_agent(
        model=llm,
        tools=[],
        system_prompt=REVIEW_SYSTEM_PROMPT,
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


def run_review_agent(student_data: dict, analysis_json: str, path_json: str) -> str:
    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
    if not _has_provider_credentials(provider):
        return _build_local_review(student_data, analysis_json, path_json)

    review_agent = create_review_agent()
    response = review_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Review the deterministic study plan and return only JSON.\n\n"
                        f"STUDENT:\n{json.dumps(student_data)}\n\n"
                        f"ANALYSIS:\n{analysis_json}\n\n"
                        f"LEARNING_PATH:\n{path_json}"
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
        return _build_local_review(student_data, analysis_json, path_json)


def run_summary_agent(student_data: dict, analysis_json: str, path_json: str, review_json: str) -> str:
    try:
        json.loads(analysis_json)
        json.loads(path_json)
        json.loads(review_json)
    except json.JSONDecodeError:
        return _build_local_summary(student_data, analysis_json, path_json, review_json)

    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
    if not _has_provider_credentials(provider):
        return _build_local_summary(student_data, analysis_json, path_json, review_json)

    summary_agent = create_summary_agent()
    response = summary_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Write the final student-facing summary in plain text.\n\n"
                        f"STUDENT:\n{json.dumps(student_data)}\n\n"
                        f"ANALYSIS:\n{analysis_json}\n\n"
                        f"LEARNING_PATH:\n{path_json}\n\n"
                        f"REVIEW:\n{review_json}"
                    ),
                }
            ]
        }
    )
    return _extract_agent_text(response).strip() or _build_local_summary(student_data, analysis_json, path_json, review_json)
