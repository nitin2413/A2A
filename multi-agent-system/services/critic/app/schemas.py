from pydantic import BaseModel


class CriticResponse(BaseModel):
    approved: bool
    feedback: str
    score: float | None