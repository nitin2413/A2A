from typing import Protocol

from shared.schemas.task import Task


class Agent(Protocol):
    async def execute(self, task: Task):
        ...