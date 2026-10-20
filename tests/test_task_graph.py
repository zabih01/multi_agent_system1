import pytest
from multi_agent.models import TaskSpec
from multi_agent.task_graph import TaskGraph


def test_graph_rejects_cycle():
    a = TaskSpec(name="a", description="a", agent_name="x")
    b = TaskSpec(name="b", description="b", agent_name="x", dependencies=[a.id])
    a.dependencies = [b.id]
    with pytest.raises(ValueError, match="cycle"):
        TaskGraph([a, b])


def test_graph_rejects_missing_dependency():
    task = TaskSpec(name="a", description="a", agent_name="x", dependencies=["missing"])
    with pytest.raises(ValueError, match="unknown dependencies"):
        TaskGraph([task])
