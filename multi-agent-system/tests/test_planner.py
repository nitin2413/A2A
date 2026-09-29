import pytest

from services.planner.app.agent import PlannerAgent
from shared.schemas.task import TaskStatus


@pytest.mark.asyncio
async def test_planner_creates_plan():
    planner = PlannerAgent()

    plan = await planner.create_plan(
        "Build a FastAPI application for MNIST classification."
    )

    assert plan.user_request == (
        "Build a FastAPI application for MNIST classification."
    )

    assert len(plan.tasks) == 3

    task_1, task_2, task_3 = plan.tasks

    assert task_1.assigned_agent == "planner"
    assert task_2.assigned_agent == "codegen"
    assert task_3.assigned_agent == "critic"

    assert task_1.status == TaskStatus.PENDING
    assert task_2.status == TaskStatus.PENDING
    assert task_3.status == TaskStatus.PENDING

    assert task_2.depends_on == [task_1.task_id]
    assert task_3.depends_on == [task_2.task_id]