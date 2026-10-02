import pytest

from services.codegen.app.agent import CodegenAgent
from shared.schemas.task import Task


@pytest.mark.asyncio
async def test_codegen_llm():
    codegen = CodegenAgent()

    task = Task(
        description=(
            "Add a function called `calculate_average` to "
            "`app/math_utils.py` that accepts a list of numbers "
            "and returns their average."
        ),
        assigned_agent="codegen",
        input_payload={
            "files": {
                "app/math_utils.py": (
                    "def add(a: float, b: float) -> float:\n"
                    "    return a + b\n"
                ),
            }
        },
        resources=[
            "Use the existing style in app/math_utils.py.",
            "Do not modify the existing add function.",
        ],
    )

    response = await codegen.execute(task)

    # Verify response structure
    assert response.summary
    assert response.patches

    # Verify every patch has the required fields
    for patch in response.patches:
        assert patch.file_path
        assert patch.patch

    # Display actual LLM output
    print("\n" + "=" * 70)
    print("CODEGEN LLM RESPONSE")
    print("=" * 70)

    print("\nSUMMARY:")
    print(response.summary)

    print("\nPATCHES:")

    for index, patch in enumerate(response.patches, start=1):
        print(f"\n--- Patch {index} ---")
        print(f"File: {patch.file_path}")
        print(patch.patch)

    print("=" * 70)