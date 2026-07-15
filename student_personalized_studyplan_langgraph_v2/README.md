# Student Personalized Study Plan - LangGraph V2

POC architecture: FastAPI exposes planner, executor, critic, summary, and workflow endpoints. LangGraph orchestrates the agents. Only the Qwen executor receives tools, and those wrappers call a separate MCP Streamable HTTP server. There is no agent fallback.

```text
POST /workflow -> planner -> executor -> critic -> summary
                              |           |
                              |           +-> revision -> planner (once)
                              +-> MCP client -> MCP server :8001/mcp
```

## Setup

```powershell
pip install -r student_personalized_studyplan_langgraph_v2/requirements.txt
```

Copy `.env.example` to `.env` and set `HUGGINGFACEHUB_API_TOKEN`. The real `.env` must not be committed.

## Run

Terminal 1:

```powershell
python -m student_personalized_studyplan_langgraph_v2.mcp_server
```

Terminal 2:

```powershell
python -m uvicorn student_personalized_studyplan_langgraph_v2.api:app --port 8000
```

Open `http://127.0.0.1:8000/docs`. `POST /workflow` returns nested, presentation-friendly JSON. Detailed exception chains are intentionally exposed for POC debugging only.

Qwen selects and calls tools, then returns `DONE`; Python maps the real MCP `ToolMessage` responses into graph state. Critic and summary receive compact evidence to conserve free inference quota. Thinking is disabled through `chat_template_kwargs.enable_thinking=false`.
