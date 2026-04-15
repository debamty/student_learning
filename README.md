# Student Learning Path Agent

This project scaffolds a LangChain-based agent that:

- collects a student's marks and study preferences
- analyzes strong and weak subjects
- creates a customized learning path
- recommends a weekly study schedule and short-term milestones

## How it works

The agent uses two domain tools:

- `analyze_marks`: identifies strengths, weak areas, average score, and subject priority
- `build_learning_path`: creates a phased study plan based on marks and available study time

The LangChain agent orchestrates those tools and returns a student-friendly response.

## Project files

- `student_learning/models.py`: Pydantic schema for student data
- `student_learning/analysis.py`: marks analysis logic
- `student_learning/learning_path.py`: study path generation logic
- `student_learning/tools.py`: LangChain tool wrappers
- `student_learning/agent.py`: LLM and agent wiring
- `student_learning/student_learning.py`: readable startup module
- `student_learning/__main__.py`: package entrypoint for `python -m student_learning`
- `student_learning/sample_data.py`: example student payload
- `student_learning/requirements.txt`: Python dependencies
- `student_learning/.env.example`: environment variables template

## Setup

```bash
pip install -r student_learning/requirements.txt
```

Copy `student_learning/.env.example` to `student_learning/.env` and configure either OpenAI or Hugging Face.

## Model provider options

### OpenAI

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

### Hugging Face

```env
LLM_PROVIDER=huggingface
HUGGINGFACEHUB_API_TOKEN=your_huggingface_token_here
HUGGINGFACE_REPO_ID=mistralai/Mixtral-8x7B-Instruct-v0.1
HUGGINGFACE_TASK=text-generation
HUGGINGFACE_MAX_NEW_TOKENS=512
```

The orchestrator remains `student_learning/agent.py`; only the LLM backend changes.

## Run

```bash
python -m student_learning
```

## Notes on Hugging Face

- The application architecture does not change when switching providers.
- Tool-calling quality depends on the Hugging Face model you choose.
- For best results, use an instruction-tuned model that behaves reliably in chat-style workflows.

## Example input

```python
sample_student = {
    "name": "Aarav",
    "grade": "8",
    "target_goal": "Improve final exam score to above 85 percent",
    "weekly_study_hours": 12,
    "preferred_style": "visual and practice-heavy",
    "marks": {
        "Mathematics": 48,
        "Science": 58,
        "English": 74,
        "Social Studies": 81,
        "Hindi": 67,
    },
}

