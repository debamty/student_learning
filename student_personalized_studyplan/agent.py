import json
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_openai import ChatOpenAI

from .analysis import build_marks_analysis
from .learning_path import build_study_path
from .models import StudentProfile
from .prompts import SYSTEM_PROMPT
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

    raise ValueError(
        "Unsupported LLM_PROVIDER. Expected 'openai' or 'huggingface'."
    )


def _build_local_fallback_response(student_data: dict) -> dict:
    student = StudentProfile.model_validate(student_data)
    analysis = build_marks_analysis(student)
    path = build_study_path(student)

    weak_subjects = ", ".join(analysis["priority_subjects"]) or "none"
    strong_subjects = ", ".join(analysis["top_strengths"]) or "none"
    weekly_plan = path["weekly_plan"]
    subject_lines = [
        f"- {item['subject']} ({item['score']}): " + " ".join(item["recommended_actions"])
        for item in path["subject_actions"]
    ]

    output = "\n".join(
        [
            f"Student: {analysis['student']} (Grade {analysis['grade']})",
            f"Goal: {analysis['target_goal']}",
            f"Average score: {analysis['average_score']}",
            f"Weak subjects: {weak_subjects}",
            f"Strong subjects: {strong_subjects}",
            "",
            "Weekly plan:",
            f"- Weak subjects: {weekly_plan['weak_subjects_hours']} hours",
            f"- Medium subjects: {weekly_plan['medium_subjects_hours']} hours",
            f"- Strong subjects: {weekly_plan['strong_subjects_hours']} hours",
            "",
            "Subject guidance:",
            *subject_lines,
        ]
    )

    return {
        "output": output,
        "raw": {
            "mode": "local-fallback",
            "analysis": analysis,
            "learning_path": path,
        },
    }


def create_student_agent():
    llm = _create_llm()
    return create_agent(
        model=llm,
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT,
        debug=True,
    )


def run_student_learningpath_langchain_agent(student_data: dict) -> dict:
    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
    if not _has_provider_credentials(provider):
        return _build_local_fallback_response(student_data)

    agent = create_student_agent()
    payload = json.dumps(student_data)
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Analyze the following student profile and create a customized learning path. "
                        "Use the available tools before answering.\n\n"
                        f"{payload}"
                    ),
                }
            ]
        }
    )
    messages = result.get("messages", [])
    final_message = messages[-1] if messages else None
    output = getattr(final_message, "content", "") if final_message else ""
    return {"output": output, "raw": result}
