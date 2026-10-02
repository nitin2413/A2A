from services.codegen.app.schemas import CodegenResponse
from shared.llm import get_llm
from shared.schemas.task import Task
from shared.workspace.context import ContextRetriever
import json


CODEGEN_SYSTEM_PROMPT = """
You are a code generation agent.

Your job is to modify an existing codebase to accomplish
the assigned task.

Rules:

1. Generate patches, not complete file contents.

2. Every patch MUST use standard unified diff format.

3. A valid patch MUST begin with file headers such as:

--- a/app/example.py
+++ b/app/example.py

4. NEVER use the following patch format:

*** Begin Patch
*** Update File:
*** End Patch

5. Do not use GitHub/Codex apply-patch syntax.

6. Use standard unified diff hunks such as:

@@ -1,3 +1,5 @@

7. Only modify files relevant to the task.

8. Preserve existing functionality unless the task requires
   changing it.

9. Use the existing project structure and conventions.

10. Do not invent project requirements.

11. Do not modify unrelated files.

12. Return a concise summary of the changes.

13. Every patch must specify its target file path.

14. Do not include Markdown code fences around patches.

15. The patch must be applicable to the provided existing
    file content.

16. If the provided context is insufficient to safely generate
    a patch, report the limitation instead of inventing code.

17. Do not introduce new behavior, fallback behavior,
    validation rules, or API changes unless required by
    the task or existing code.

18. Do not invent fallback behavior.

19. Do not change behavior that was not requested.

20. Each FilePatch must contain exactly one standard
    unified diff for its target file.
"""


class CodegenAgent():
    def __init__(self,context_retriever: ContextRetriever):
        self.context_retriever = context_retriever

    async def execute(self, task:Task)->CodegenResponse:

        llm = get_llm("codegen")
        structured_llm = llm.with_structured_output(CodegenResponse)

        files = self.context_retriever.retrieve(
            task.resources
        )

        human_message = f"""
        Task : 
        {task.description}

        Existing Files:
        {json.dumps(files, indent=2)}

        Resources:
        {json.dumps(task.resources, indent=2)} 
        """
        response : CodegenResponse = await structured_llm.ainvoke(
            [
                ("system",  CODEGEN_SYSTEM_PROMPT ),
                ("human" , human_message),
            ]
        )
        return response