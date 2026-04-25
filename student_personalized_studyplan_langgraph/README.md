# Student Personalized Study Plan — LangGraph Multi-Agent

This package implements a personalized student study planner using a Lang Graph multi-agent flow.

- `agent.py` initializes three specialized agents: analysis, planning, and summary.
- `graph.py` builds a `StateGraph` that routes data through each agent node.
- `tools.py` exposes domain tools for student performance analysis and study path generation.
- `sample_data.py` includes example student inputs.

## Folder name suggestion
Use `student_personalized_studyplan_langgraph` for the new Lang Graph version.

## Setup

```bash
pip install -r student_personalized_studyplan_langgraph/requirements.txt
```

Copy `.env.example` into `.env` and configure provider credentials.

## Run

```bash
python -m student_personalized_studyplan_langgraph
```
