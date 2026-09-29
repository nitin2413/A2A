import pytest
import asyncio
import time

from orchestrator.app.dispatcher import TaskDispatcher
from orchestrator.app.graph import validate_plan
from orchestrator.app.exceptions import (
    UnknownAgentError,
    PlanGraphError,
)
from shared.schemas.task import (
    Task,
    Plan,
    TaskStatus,
    PlanStatus,
)

#
# class FakeAgent:
#     async def execute(self, task: Task):
#         return {
#             "message": f"Executed {task.description}"
#         }
#
#
# @pytest.mark.asyncio
# async def test_single_task_success():
#     # Arrange
#     task = Task(
#         description="Test task",
#         assigned_agent="fake",
#     )
#
#     plan = Plan(
#         user_request="Run a test task",
#         tasks=[task],
#     )
#
#     agents = {
#         "fake": FakeAgent()
#     }
#
#     dispatcher = TaskDispatcher(agents)
#
#     # Act
#     await dispatcher.execute_plan(plan)
#
#     # Assert
#     assert task.status == TaskStatus.DONE
#     assert task.attempt_count == 1
#     assert task.output_payload == {
#         "message": "Executed Test task"
#     }
#
#     assert plan.status == PlanStatus.DONE
#
# import asyncio
# import time
#
# import pytest
#
# from orchestrator.app.dispatcher import TaskDispatcher
# from shared.schemas.task import (
#     Plan,
#     PlanStatus,
#     Task,
#     TaskStatus,
# )
#

class FakeAgent:
    async def execute(self, task: Task):
        return {
            "message": f"Executed {task.description}"
        }


class SlowFakeAgent:
    async def execute(self, task: Task):
        await asyncio.sleep(1)

        return {
            "message": f"Executed {task.description}"

        }

class TrackingAgent:
    def __init__(self):
        self.execution_order = []

    async def execute(self, task: Task):
        self.execution_order.append(task.description)

        return {
            "message": f"Executed {task.description}"
        }


@pytest.mark.asyncio
async def test_single_task_success():
    # Arrange
    task = Task(
        description="Test task",
        assigned_agent="fake",
    )

    plan = Plan(
        user_request="Run a test task",
        tasks=[task],
    )

    agents = {
        "fake": FakeAgent()
    }

    dispatcher = TaskDispatcher(agents)

    # Act
    await dispatcher.execute_plan(plan)

    # Assert
    assert task.status == TaskStatus.DONE
    assert task.attempt_count == 1
    assert task.output_payload == {
        "message": "Executed Test task"
    }

    assert plan.status == PlanStatus.DONE


@pytest.mark.asyncio
async def test_concurrent_tasks():
    # Arrange
    task_a = Task(
        description="Task A",
        assigned_agent="slow_fake",
    )

    task_b = Task(
        description="Task B",
        assigned_agent="slow_fake",
    )

    plan = Plan(
        user_request="Run two independent tasks",
        tasks=[task_a, task_b],
    )

    agents = {
        "slow_fake": SlowFakeAgent()
    }

    dispatcher = TaskDispatcher(agents)

    # Act
    start = time.perf_counter()

    await dispatcher.execute_plan(plan)

    elapsed = time.perf_counter() - start

    # Assert
    assert task_a.status == TaskStatus.DONE
    assert task_b.status == TaskStatus.DONE

    assert task_a.attempt_count == 1
    assert task_b.attempt_count == 1

    assert task_a.output_payload == {
        "message": "Executed Task A"
    }

    assert task_b.output_payload == {
        "message": "Executed Task B"
    }

    assert plan.status == PlanStatus.DONE

    # Both tasks take ~1 second, so concurrent execution
    # should finish well below 2 seconds.
    assert elapsed < 1.5

@pytest.mark.asyncio
async def test_sequential_dependencies():
    # Arrange
    tracking_agent = TrackingAgent()

    task_a = Task(
        description="Task A",
        assigned_agent="tracker",
    )

    task_b = Task(
        description="Task B",
        assigned_agent="tracker",
        depends_on=[task_a.task_id],
    )

    task_c = Task(
        description="Task C",
        assigned_agent="tracker",
        depends_on=[task_b.task_id],
    )

    plan = Plan(
        user_request="Run sequential tasks",
        tasks=[
            task_a,
            task_b,
            task_c,
        ],
    )

    agents = {
        "tracker": tracking_agent
    }

    dispatcher = TaskDispatcher(agents)

    # Act
    await dispatcher.execute_plan(plan)

    # Assert
    assert tracking_agent.execution_order == [
        "Task A",
        "Task B",
        "Task C",
    ]

    assert task_a.status == TaskStatus.DONE
    assert task_b.status == TaskStatus.DONE
    assert task_c.status == TaskStatus.DONE

    assert plan.status == PlanStatus.DONE

@pytest.mark.asyncio
async def test_parallel_tasks_then_dependent_task():
    class TrackingAgent:
        def __init__(self):
            self.execution_order = []

        async def execute(self, task: Task):
            self.execution_order.append(task.description)

            if task.description in ("Task A", "Task B"):
                await asyncio.sleep(0.5)

            return {
                "message": f"Executed {task.description}"
            }

    agent = TrackingAgent()

    task_a = Task(
        description="Task A",
        assigned_agent="tracker",
    )

    task_b = Task(
        description="Task B",
        assigned_agent="tracker",
    )

    task_c = Task(
        description="Task C",
        assigned_agent="tracker",
        depends_on=[
            task_a.task_id,
            task_b.task_id,
        ],
    )

    plan = Plan(
        user_request="Run parallel tasks then dependent task",
        tasks=[task_a, task_b, task_c],
    )

    dispatcher = TaskDispatcher({
        "tracker": agent
    })

    await dispatcher.execute_plan(plan)

    assert task_a.status == TaskStatus.DONE
    assert task_b.status == TaskStatus.DONE
    assert task_c.status == TaskStatus.DONE

    assert plan.status == PlanStatus.DONE

    # C must execute after both A and B.
    assert agent.execution_order.index("Task C") > \
           agent.execution_order.index("Task A")

    assert agent.execution_order.index("Task C") > \
           agent.execution_order.index("Task B")

@pytest.mark.asyncio
async def test_retry_then_success():
    class RetryAgent:
        def __init__(self):
            self.calls = 0

        async def execute(self, task: Task):
            self.calls += 1

            if self.calls == 1:
                raise RuntimeError("Temporary failure")

            return {
                "message": "Success after retry"
            }

    agent = RetryAgent()

    task = Task(
        description="Retry task",
        assigned_agent="retry",
        max_attempts=3,
    )

    plan = Plan(
        user_request="Test retry",
        tasks=[task],
    )

    dispatcher = TaskDispatcher({
        "retry": agent
    })

    await dispatcher.execute_plan(plan)

    assert agent.calls == 2
    assert task.attempt_count == 2
    assert task.status == TaskStatus.DONE

    assert task.output_payload == {
        "message": "Success after retry"
    }

    assert plan.status == PlanStatus.DONE

@pytest.mark.asyncio
async def test_retry_exhaustion():
    class FailingAgent:
        def __init__(self):
            self.calls = 0

        async def execute(self, task: Task):
            self.calls += 1
            raise RuntimeError("Permanent failure")

    agent = FailingAgent()

    task = Task(
        description="Always failing task",
        assigned_agent="failing",
        max_attempts=3,
    )

    plan = Plan(
        user_request="Test retry exhaustion",
        tasks=[task],
    )

    dispatcher = TaskDispatcher({
        "failing": agent
    })

    with pytest.raises(RuntimeError):
        await dispatcher.execute_plan(plan)

    assert agent.calls == 3
    assert task.attempt_count == 3
    assert task.status == TaskStatus.FAILED
    assert task.error == "Permanent failure"

    assert plan.status == PlanStatus.FAILED

@pytest.mark.asyncio
async def test_failed_dependency_blocks_task():
    class SelectiveAgent:
        def __init__(self):
            self.executed = []

        async def execute(self, task: Task):
            self.executed.append(task.description)

            if task.description == "Task A":
                raise RuntimeError("Task A failed")

            return {
                "message": f"Executed {task.description}"
            }

    agent = SelectiveAgent()

    task_a = Task(
        description="Task A",
        assigned_agent="agent",
        max_attempts=1,
    )

    task_b = Task(
        description="Task B",
        assigned_agent="agent",
        depends_on=[task_a.task_id],
    )

    plan = Plan(
        user_request="Test blocked dependency",
        tasks=[task_a, task_b],
    )

    dispatcher = TaskDispatcher({
        "agent": agent
    })

    with pytest.raises(RuntimeError):
        await dispatcher.execute_plan(plan)

    assert task_a.status == TaskStatus.FAILED
    assert task_b.status == TaskStatus.BLOCKED

    assert "Task A" in agent.executed
    assert "Task B" not in agent.executed

    assert plan.status == PlanStatus.FAILED

@pytest.mark.asyncio
async def test_blocked_tasks_cascade():
    class FailingAgent:
        async def execute(self, task: Task):
            if task.description == "Task A":
                raise RuntimeError("A failed")

            raise AssertionError(
                f"{task.description} should never execute"
            )

    agent = FailingAgent()

    task_a = Task(
        description="Task A",
        assigned_agent="agent",
        max_attempts=1,
    )

    task_b = Task(
        description="Task B",
        assigned_agent="agent",
        depends_on=[task_a.task_id],
    )

    task_c = Task(
        description="Task C",
        assigned_agent="agent",
        depends_on=[task_b.task_id],
    )

    plan = Plan(
        user_request="Test blocked cascade",
        tasks=[task_a, task_b, task_c],
    )

    dispatcher = TaskDispatcher({
        "agent": agent
    })

    with pytest.raises(RuntimeError):
        await dispatcher.execute_plan(plan)

    assert task_a.status == TaskStatus.FAILED
    assert task_b.status == TaskStatus.BLOCKED
    assert task_c.status == TaskStatus.BLOCKED

    assert plan.status == PlanStatus.FAILED

@pytest.mark.asyncio
async def test_unknown_agent():
    task = Task(
        description="Unknown agent task",
        assigned_agent="does_not_exist",
    )

    plan = Plan(
        user_request="Test unknown agent",
        tasks=[task],
    )

    dispatcher = TaskDispatcher({})

    with pytest.raises(UnknownAgentError):
        await dispatcher.execute_plan(plan)

def test_unknown_dependency():
    task = Task(
        description="Task A",
        assigned_agent="fake",
    )

    unknown_dependency = uuid4()

    task.depends_on = [unknown_dependency]

    plan = Plan(
        user_request="Invalid graph",
        tasks=[task],
    )

    with pytest.raises(PlanGraphError):
        validate_plan(plan)

from uuid import uuid4

def test_cycle_detection():
    task_a = Task(
        description="Task A",
        assigned_agent="fake",
    )

    task_b = Task(
        description="Task B",
        assigned_agent="fake",
    )

    task_c = Task(
        description="Task C",
        assigned_agent="fake",
    )

    task_a.depends_on = [task_c.task_id]
    task_b.depends_on = [task_a.task_id]
    task_c.depends_on = [task_b.task_id]

    plan = Plan(
        user_request="Cyclic plan",
        tasks=[task_a, task_b, task_c],
    )

    with pytest.raises(PlanGraphError):
        validate_plan(plan)
