from fastapi import FastAPI
from multi_agent.main import build_system
from multi_agent.models import TaskSpec

app = FastAPI(title="Multi-Agent Orchestration API", version="0.1.0")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/agents")
async def agents():
    _, registry, _ = build_system()
    return {"agents": registry.names()}

@app.get("/tasks/history")
async def task_history():
    _, _, store = build_system()
    return [result.model_dump(mode="json") for result in store.list_results()]
