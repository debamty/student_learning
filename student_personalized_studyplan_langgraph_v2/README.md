# Student Personalized Study Plan - LangGraph V2

This version keeps deterministic academic logic where it belongs and uses LLM reasoning where it adds the most value.

Flow:
- `analysis` node computes a deterministic performance analysis
- `planning` node computes a deterministic study path
- `review` agent critiques alignment between the student profile and the plan
- `summary` agent writes the final student-facing report

Why this version is better:
- it is more honest about where reasoning happens
- it introduces a real review stage instead of labeling every step an agent
- it still remains simple enough for a POC or portfolio demo

## Setup

```bash
pip install -r student_personalized_studyplan_langgraph_v2/requirements.txt
```

Copy `.env.example` into `.env` and configure provider credentials.

## Run

```bash
python -m student_personalized_studyplan_langgraph_v2
```
