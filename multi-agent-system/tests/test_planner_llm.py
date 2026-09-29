import pytest

from services.planner.app.agent import PlannerAgent
from orchestrator.app.graph import validate_plan


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "user_request",
    [
        "Build a FastAPI application for MNIST classification.",
        "Create a Python web scraper that collects product names and prices.",
        "Build a RAG system that answers questions from PDF documents.",
    ],
)
async def test_planner_llm(user_request: str):
    planner = PlannerAgent()

    plan = await planner.create_plan(user_request)

    # Basic Plan validation
    assert plan.user_request == user_request
    assert len(plan.tasks) > 0

    # Every task should have a description
    for task in plan.tasks:
        assert task.description.strip()
        assert task.assigned_agent in {
            "planner",
            "codegen",
            "critic",
        }

    # Every dependency should reference an existing task
    task_ids = {task.task_id for task in plan.tasks}

    for task in plan.tasks:
        for dependency in task.depends_on:
            assert dependency in task_ids

    # Validate the complete execution graph
    validate_plan(plan)
    print("\nUSER REQUEST:")
    print(user_request)

    print("\nGENERATED PLAN:")

    for task in plan.tasks:
        print(
            f"Task {task.task_id}: "
            f"[{task.assigned_agent}] "
            f"{task.description}"
        )

        print(
            f"  depends_on: {task.depends_on}"
        )