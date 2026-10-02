import pytest

from services.codegen.app.agent import CodegenAgent
from shared.schemas.task import Task
from shared.workspace.context import ContextRetriever
from shared.workspace.manager import WorkspaceManager


@pytest.mark.asyncio
async def test_codegen_to_workspace(tmp_path):
    workspace = WorkspaceManager(str(tmp_path))

    workspace.write_file(
        "app/math.py",
        """def add(a, b):
    return a + b
""",
    )

    context_retriever = ContextRetriever(workspace)

    codegen = CodegenAgent(context_retriever)

    task = Task(
        description="Add a multiply function to app/math.py",
        assigned_agent="codegen",
        resources=["app/math.py"],
    )

    response = await codegen.execute(task)

    assert response.patches

    for patch in response.patches:
        workspace.apply_patch(patch)

    updated = workspace.read_file("app/math.py")

    assert "def multiply" in updated