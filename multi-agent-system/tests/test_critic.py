import pytest

from services.critic.app.agent import CriticAgent
from shared.workspace.context import ContextRetriever
from shared.workspace.manager import WorkspaceManager
from shared.schemas.task import Task


@pytest.mark.asyncio
async def test_critic_approves_correct_code(tmp_path):
    workspace = WorkspaceManager(str(tmp_path))

    workspace.write_file(
        "app/math.py",
        """def add(a, b):
    return a + b


def multiply(a, b):
    return a * b
""",
    )

    context_retriever = ContextRetriever(workspace)
    critic = CriticAgent(context_retriever)

    task = Task(
        description="Add a multiply function to app/math.py",
        assigned_agent="critic",
        resources=["app/math.py"],
    )

    critique = await critic.execute(
        task,
        ["app/math.py"],
    )

    assert critique.approved is True
    assert critique.target_task_id == task.task_id
    assert critique.feedback

@pytest.mark.asyncio
async def test_critic_rejects_incorrect_code(tmp_path):
    workspace = WorkspaceManager(str(tmp_path))

    workspace.write_file(
        "app/math.py",
        """def add(a, b):
    return a + b


def multiply(a, b):
    return a + b
""",
    )

    context_retriever = ContextRetriever(workspace)
    critic = CriticAgent(context_retriever)

    task = Task(
        description="Add a multiply function to app/math.py",
        assigned_agent="critic",
        resources=["app/math.py"],
    )

    critique = await critic.execute(
        task,
        ["app/math.py"],
    )

    assert critique.approved is False
    assert critique.target_task_id == task.task_id
    assert critique.feedback