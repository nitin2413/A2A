from shared.schemas.task import Plan , Task , TaskStatus
from orchestrator.app.exceptions import PlanGraphError

def validate_plan(plan : Plan)-> None:
    task_ids = set()
    errors =[]
    duplicates = set()
    for task in plan.tasks:
        if task.task_id in task_ids:
            duplicates.add(task.task_id)
        task_ids.add(task.task_id)

    if duplicates:
        errors.append(
            f"Duplicate task IDs found: {', '.join(str(task_id) for task_id in duplicates)}"
        )

    for task in plan.tasks:
        for dependency in task.depends_on:
            if dependency not in task_ids:
                errors.append(
                    f"Task {task.task_id} depends on unknown task {dependency}"
                )
            if task.task_id == dependency:
                errors.append(
                    f"Task {task.task_id} depends on itself {dependency}"
                )
                continue

    visited = set()
    current_path = set()

    task_map = {task.task_id : task for task in plan.tasks}

    def visit(task_id):
        if task_id in current_path:
            errors.append(
                f"Cycle detected involving task {task_id}"
            )
            return
        if task_id in visited:
            return
        current_path.add(task_id)
        task = task_map[task_id]
        for dependency in task.depends_on:
            # Unknown dependencies were already reported above
            if dependency in task_map:
                visit(dependency)

        current_path.remove(task_id)
        visited.add(task_id)

    for task_id in task_ids:
        visit(task_id)

    if errors:
        raise PlanGraphError(
            "Plan validation failed:\n- " + "\n- ".join(errors)
        )

def get_ready_tasks(plan: Plan) -> list[Task]:
    ready_tasks = []

    task_map = {task.task_id:task for task in plan.tasks}
    for task in plan.tasks:
        if task.status != TaskStatus.PENDING:
            continue

        dependency_done = all(
            task_map[dependency].status == TaskStatus.DONE
            for dependency in task.depends_on
        )
        if dependency_done:
            ready_tasks.append(task)
    return ready_tasks

def get_blocked_tasks(plan : Plan) -> list[Task]:
    blocked_task = []
    task_map = {task.task_id : task for task in plan.tasks}
    for task in plan.tasks:
        if task.status != TaskStatus.PENDING:
            continue
        dependency_block = any(
        task_map[dependency].status in (TaskStatus.FAILED , TaskStatus.BLOCKED,)
            for dependency in task.depends_on
        )
        if dependency_block:
            blocked_task.append(task)
    return blocked_task