from shared.llm import get_llm
from shared.schemas.task import Task , Critique
from shared.workspace.context import ContextRetriever
from services.critic.app.schemas import CriticResponse
import json

CRITIC_SYSTEM_PROMPT = """
You are a code review agent.

Your job is to review the implementation of a software task.

Evaluate whether the modified code correctly satisfies the task.

Review for:

1. Correctness
2. Missing requirements
3. Obvious bugs
4. Unintended behavior changes
5. Consistency with the existing code
6. Unnecessary changes
7. Maintainability

Rules:

- Review the actual code provided.
- Do not assume code exists that was not provided.
- Do not invent requirements.
- Do not modify files.
- Do not generate patches.
- Be specific about problems.
- If the implementation is correct, approve it.
- If changes are required, clearly explain what is wrong.
"""

class CriticAgent():
    def __init__(self , context_retriever : ContextRetriever):
        self.context_retriever = context_retriever

    async def execute(self, task:Task , changed_files : list[str])->Critique:
        files = self.context_retriever.retrieve(changed_files)

        llm = get_llm("critic")
        structure_llm = llm.with_structured_output(CriticResponse)

        human_message = f"""
        Task :
        {task.description}
        
        changed_file :
        {json.dumps(files , indent=2)}
        
        Review the implementation and determine whether
        the task has been correctly completed.
        """

        response : CriticResponse = await structure_llm.ainvoke(
            [
                ("system" , CRITIC_SYSTEM_PROMPT),
                ("human" , human_message)
            ]
        )
        
        return Critique(
            approved=response.approved,
            feedback=response.feedback,
            score=response.score,
            target_task_id=task.task_id,
        )
