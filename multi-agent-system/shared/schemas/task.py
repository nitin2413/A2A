from enum import Enum
from datetime import datetime , timezone
from typing import Any
from uuid import UUID , uuid4

from pydantic import BaseModel, Field

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    FAILED = "failed"
    BLOCKED = "blocked"
    NEEDS_RETRY = "needs_retry"

class Task(BaseModel):
    task_id: UUID = Field(default_factory=uuid4)
    parent_task_id: UUID | None = None

    description: str
    assigned_agent: str
    status: TaskStatus = TaskStatus.PENDING

    depends_on: list[UUID] = Field(default_factory=list)
    resources: list[str] = Field(default_factory=list)

    input_payload: dict[str , Any] = Field(default_factory=dict)
    output_payload : dict[str , Any] | None = None

    attempt_count : int = 0 
    max_attempts : int = 3

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    error: str | None = None   

    def update_status(self, new_status: TaskStatus):
        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)

class PlanStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    FAILED = "failed"
    NEEDS_RETRY = "needs_retry"


class Plan(BaseModel):
    plan_id : UUID = Field(default_factory = uuid4)    
    user_request : str
    tasks : list[Task] = Field(default_factory=list)
    status : PlanStatus = PlanStatus.PENDING
    created_at : datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at : datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def update_status(self, status: PlanStatus) -> None:
        self.status = status
        self.updated_at = datetime.now(timezone.utc)

class Critique(BaseModel):
    approved : bool
    feedback : str    
    score : float | None = None
    target_task_id : UUID 
    created_at : datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


