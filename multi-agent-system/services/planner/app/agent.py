from shared.schemas.task import Plan , Task
from services.planner.app.schemas import PlannerResponse
from uuid import UUID , uuid4
from shared.llm import get_llm

class InvalidPlannerResponse(Exception):
    pass

def convert_int_to_uuid(user_request:str , response:PlannerResponse) -> Plan:
    task_ids = [task.task_id for task in response.tasks]

    if len(task_ids) != len(set(task_ids)):
        raise InvalidPlannerResponse(
            "Planner returned duplicate task IDs."
        )

    task_id_set = set(task_ids)

    # Validate dependencies before creating UUIDs
    for task in response.tasks:
        for dependency_id in task.depends_on:
            if dependency_id not in task_id_set:
                raise InvalidPlannerResponse(
                    f"Task {task.task_id} depends on "
                    f"unknown task {dependency_id}."
                )

            if dependency_id == task.task_id:
                raise InvalidPlannerResponse(
                    f"Task {task.task_id} depends on itself."
                )
    id_mapping : dict[int , UUID] = {
        task.task_id : uuid4()
        for task in response.tasks
    }
    tasks = []
    for task in response.tasks:
        task = Task(
            task_id=id_mapping[task.task_id],
            description=task.description,
            assigned_agent=task.assigned_agent,
            depends_on=[
                id_mapping[dependency_id]
                for dependency_id in task.depends_on
            ],
        )
        tasks.append(task)
    return Plan(
            user_request = user_request,
            tasks = tasks
    )


PLANNER_SYSTEM_PROMPT = """
You are a planning agent in a multi-agent software system.

Your job is to decompose the user's request into a clear sequence
of executable tasks.

Available agents:
- planner: planning and decomposition
- codegen: writing or modifying code
- critic: reviewing and testing work

Rules:
1. Create only tasks that are necessary to accomplish the request.
2. Every task must have a unique integer task_id.
3. depends_on must contain only existing task IDs.
4. Do not create circular dependencies.
5. Assign each task to the most appropriate available agent.
6. Do not execute any task.
7. Do not generate UUIDs.
8. Keep each task specific and executable.
9. Do not choose specific libraries, frameworks, databases, models,
   or implementation technologies unless:
   - the user explicitly requested them, or
   - an existing project constraint requires them.
10. Do not create setup or housekeeping tasks such as requirements.txt,
    dependency files, README files, configuration files, or documentation
    unless they are explicitly required by the user's request.
11. Dependencies must represent direct information or execution
    prerequisites, not simply chronological ordering.
12. Avoid unnecessary dependency edges.
13. Prefer parallel tasks when they are genuinely independent.
14. Each task should contribute directly to the user's requested outcome.
15. Do not add tasks merely because they are common software-development
    practices.
"""


class PlannerAgent():
    async def create_plan(self, user_request:str)->Plan:
        llm = get_llm("planner")

        structured_llm = llm.with_structured_output(PlannerResponse)

        response : PlannerResponse = await structured_llm.ainvoke(
            [
                ("system" ,PLANNER_SYSTEM_PROMPT),
                ("user",user_request),
            ]
        )

        plan = convert_int_to_uuid(
            user_request,
            response,
        )
        return plan
        # task1 = Task(
        #     description="Analyze the user request and identify the required work.",
        #     assigned_agent="planner",
        # )
        # task2 = Task(
        #     description="Implement the solution based on the requirements.",
        #     assigned_agent="codegen",
        #     depends_on=[task1.task_id],
        # )
        # task3 = Task(
        #     description="Review the implementation and identify issues.",
        #     assigned_agent="critic",
        #     depends_on=[task2.task_id],
        # )
        #
        # return Plan(
        #     user_request = user_request,
        #     tasks=[task1 , task2 ,task3 ],
        # )