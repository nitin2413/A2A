# import asyncio
# from shared.schemas.task import Task, TaskStatus , Plan , PlanStatus
# from .graph import get_ready_tasks , validate_plan , get_blocked_tasks
#
#
# class TaskDispatcher():
#
#     def __init__(self, agents:dict):
#         self.agents = agents
#
#     async def execute_task(self , task : Task):
#         agent_name = task.assigned_agent
#
#         if agent_name not in self.agents:
#             raise UnknownAgentError(
#                 f"Unknown agent: {agent_name}"
#             )
#
#         agent = self.agents[task.assigned_agent]
#         # a place holder
#         task.update_status(TaskStatus.IN_PROGRESS)
#         task.attempt_count += 1
#
#         try:
#             result = await agent.execute(task)
#             task.output_payload = result
#             task.update_status(TaskStatus.DONE)
#
#             return result
#
#         except Exception as e:
#             task.error = str(e)
#
#             if task.attempt_count >= task.max_attempts:
#                 task.update_status(TaskStatus.FAILED)
#             else:
#                 task.update_status(TaskStatus.NEEDS_RETRY)
#
#             raise
#
#     async def dispatch_task(self , task : Task):
#         base_delay = 0.1
#         while True:
#             try :
#                 return await self.execute_task(task)
#             except Exception:
#                 if task.status == TaskStatus.NEEDS_RETRY:
#                     delay = base_delay * (2 ** (task.attempt_count - 1))
#                     await asyncio.sleep(delay)
#                     continue
#                 else:
#                     raise
#
#
#     async def dispatch_ready_tasks(self , plan:Plan):
#         ready_task= get_ready_tasks(plan)
#         coroutines = [self.dispatch_task(task) for task in ready_task]
#         results = await asyncio.gather(*coroutines,return_exceptions=True)
#         for result in results:
#             if isinstance(result, Exception):
#                 update_plan_status(plan)
#                 raise result
#
#     async def execute_plan(self, plan: Plan):
#         validate_plan(plan)
#         plan.update_status(PlanStatus.IN_PROGRESS)
#
#         terminal_exception = None
#
#         while True:
#             ready_task = get_ready_tasks(plan)
#
#             if ready_task:
#                 results = await self.dispatch_ready_tasks(plan)
#
#                 for result in results:
#                     if isinstance(result, Exception):
#                         terminal_exception = result
#
#                 continue
#
#             blocked_task = get_blocked_tasks(plan)
#
#             if blocked_task:
#                 for task in blocked_task:
#                     task.update_status(TaskStatus.BLOCKED)
#                 continue
#
#             unfinished_tasks = [
#                 task
#                 for task in plan.tasks
#                 if task.status not in (
#                     TaskStatus.DONE,
#                     TaskStatus.FAILED,
#                     TaskStatus.BLOCKED,
#                 )
#             ]
#
#             if not unfinished_tasks:
#                 break
#
#             raise RuntimeError(
#                 "Plan execution is stuck: "
#                 "no ready or blocked tasks, but unfinished tasks remain."
#             )
#
#         update_plan_status(plan)
#
#         if terminal_exception:
#             raise terminal_exception
#
#
# def update_plan_status(plan: Plan) -> None:
#     if any(task.status == TaskStatus.FAILED for task in plan.tasks):
#         plan.update_status(PlanStatus.FAILED)
#         return
#     if all(task.status == TaskStatus.DONE for task in plan.tasks):
#         plan.update_status(PlanStatus.DONE)
#         return
#     plan.update_status(PlanStatus.IN_PROGRESS)

import asyncio

from orchestrator.app.exceptions import UnknownAgentError
from orchestrator.app.graph import (
    validate_plan,
    get_ready_tasks,
    get_blocked_tasks,
)
from shared.schemas.task import (
    Task,
    Plan,
    TaskStatus,
    PlanStatus,
)
from shared.agents.protocol import Agent


def update_plan_status(plan: Plan) -> None:
    if any(task.status == TaskStatus.FAILED for task in plan.tasks):
        plan.update_status(PlanStatus.FAILED)
        return

    if all(task.status == TaskStatus.DONE for task in plan.tasks):
        plan.update_status(PlanStatus.DONE)
        return

    plan.update_status(PlanStatus.IN_PROGRESS)


class TaskDispatcher:

    def __init__(self, agents: dict[str , Agent]):
        self.agents = agents

    async def execute_task(self, task: Task):
        agent_name = task.assigned_agent

        if agent_name not in self.agents:
            raise UnknownAgentError(
                f"Unknown agent: {agent_name}"
            )

        agent = self.agents[agent_name]

        task.update_status(TaskStatus.IN_PROGRESS)
        task.attempt_count += 1

        try:
            result = await agent.execute(task)

            task.output_payload = result
            task.update_status(TaskStatus.DONE)

            return result

        except Exception as e:
            task.error = str(e)

            if task.attempt_count >= task.max_attempts:
                task.update_status(TaskStatus.FAILED)
            else:
                task.update_status(TaskStatus.NEEDS_RETRY)

            raise

    async def dispatch_task(self, task: Task):
        base_delay = 0.1

        while True:
            try:
                return await self.execute_task(task)

            except Exception:
                if task.status == TaskStatus.NEEDS_RETRY:
                    delay = base_delay * (
                        2 ** (task.attempt_count - 1)
                    )

                    await asyncio.sleep(delay)
                    continue

                raise

    async def dispatch_ready_tasks(self, plan: Plan):
        ready_tasks = get_ready_tasks(plan)

        coroutines = [
            self.dispatch_task(task)
            for task in ready_tasks
        ]

        return await asyncio.gather(
            *coroutines,
            return_exceptions=True,
        )

    async def execute_plan(self, plan: Plan):
        validate_plan(plan)

        plan.update_status(PlanStatus.IN_PROGRESS)

        terminal_exception = None

        while True:

            # 1. Find tasks whose dependencies are complete.
            ready_tasks = get_ready_tasks(plan)

            if ready_tasks:
                results = await self.dispatch_ready_tasks(plan)

                # Remember terminal failures, but DON'T raise yet.
                # We need another loop iteration so dependent tasks
                # can become BLOCKED.
                for result in results:
                    if isinstance(result, Exception):
                        terminal_exception = result

                continue

            # 2. Find tasks blocked by FAILED/BLOCKED dependencies.
            blocked_tasks = get_blocked_tasks(plan)

            if blocked_tasks:
                for task in blocked_tasks:
                    task.update_status(TaskStatus.BLOCKED)

                # Continue so blocking can cascade:
                #
                # A FAILED
                #     ↓
                # B BLOCKED
                #     ↓
                # C BLOCKED
                #
                continue

            # 3. Check whether everything has reached a terminal state.
            unfinished_tasks = [
                task
                for task in plan.tasks
                if task.status not in (
                    TaskStatus.DONE,
                    TaskStatus.FAILED,
                    TaskStatus.BLOCKED,
                )
            ]

            if not unfinished_tasks:
                break

            # 4. Nothing can execute and something is still pending.
            raise RuntimeError(
                "Plan execution is stuck: "
                "no ready or blocked tasks, "
                "but unfinished tasks remain."
            )

        # 5. Finalize the plan status.
        update_plan_status(plan)

        # 6. Only raise AFTER all dependent tasks have been
        #    given a chance to become BLOCKED.
        if terminal_exception:
            raise terminal_exception