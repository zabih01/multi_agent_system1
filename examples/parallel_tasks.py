import asyncio
from multi_agent.main import build_system
from multi_agent.models import TaskSpec

async def main():
    orchestrator, _, _ = build_system()
    tasks = [
        TaskSpec(name="research-a", description="Summarize async task scheduling.", agent_name="research"),
        TaskSpec(name="analysis-b", description="List common scheduler failure modes.", agent_name="analysis"),
        TaskSpec(name="review", description="Review both outputs.", agent_name="reviewer"),
    ]
    tasks[2].dependencies = [tasks[0].id, tasks[1].id]
    report = await orchestrator.run_objective("Parallel research demo", tasks)
    print(report.model_dump_json(indent=2))

if __name__ == "__main__":
    asyncio.run(main())
