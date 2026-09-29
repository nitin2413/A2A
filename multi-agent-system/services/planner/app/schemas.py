from pydantic import BaseModel , Field
from typing import Literal

AgentName = Literal["planner", "codegen", "critic"]

class PlannedTask(BaseModel):
    task_id : int
    description : str
    assigned_agent: AgentName
    depends_on : list[int] # = Field(default_factory=list)
    # model consider depends_on option causing error
    # by removing it we solve the problem.
    # if there is any task with none dependency then the llm return empty list

class PlannerResponse(BaseModel):
    tasks : list[PlannedTask]

'''
Why use int IDs here?
Your actual Task uses UUIDs:
task_id: UUID


But the LLM shouldn't have to generate UUIDs.
Instead, let the LLM produce:
Task 1
Task 2 → depends on Task 1
Task 3 → depends on Task 2

Then our application converts those temporary IDs into real UUIDs:
LLM output

1 → "Implement model"
2 → "Create API", depends_on=[1]

             ↓

Application conversion

UUID-A → "Implement model"
UUID-B → "Create API", depends_on=[UUID-A]

This is an important boundary:
LLM decides the plan. Application code owns identity and validation.

The LLM should not be trusted to generate internal UUIDs.
'''