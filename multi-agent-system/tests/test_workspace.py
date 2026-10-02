import pytest

from shared.workspace.manager import WorkspaceError, WorkspaceManager
from shared.workspace.context import ContextRetriever

def test_read_file(tmp_path):
    # Create a temporary workspace
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    # Create a real file inside the workspace
    app_dir = workspace / "app"
    app_dir.mkdir()

    math_file = app_dir / "math_utils.py"

    expected_content = (
        "def add(a, b):\n"
        "    return a + b\n"
    )

    math_file.write_text(expected_content)

    # Create our WorkspaceManager
    manager = WorkspaceManager(str(workspace))

    # Read the file through WorkspaceManager
    content = manager.read_file("app/math_utils.py")

    # Verify we got the correct content
    assert content == expected_content


def test_read_file_rejects_path_traversal(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    manager = WorkspaceManager(str(workspace))

    with pytest.raises(WorkspaceError):
        manager.read_file("../secret.txt")


def test_write_file_rejects_path_traversal(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    manager = WorkspaceManager(str(workspace))

    with pytest.raises(WorkspaceError):
        manager.write_file(
            "../secret.txt",
            "malicious content",
        )

def test_list_files(tmp_path):
    workspace = tmp_path / "workspace"

    (workspace / "app").mkdir(parents=True)
    (workspace / "tests").mkdir(parents=True)
    (workspace / ".venv").mkdir(parents=True)
    (workspace / ".git").mkdir(parents=True)
    (workspace / "app" / "__pycache__").mkdir(parents=True)

    (workspace / "app" / "main.py").write_text(
        "print('hello')"
    )
    (workspace / "app" / "model.py").write_text(
        "class Model:\n    pass\n"
    )
    (workspace / "tests" / "test_main.py").write_text(
        "def test_main():\n    pass\n"
    )

    # These should be ignored.
    (workspace / ".venv" / "config.py").write_text(
        "secret"
    )
    (workspace / ".git" / "config").write_text(
        "git config"
    )
    (workspace / "app" / "__pycache__" / "cache.pyc").write_text(
        "cache"
    )

    manager = WorkspaceManager(str(workspace))

    files = manager.list_files()

    assert files == [
        "app/main.py",
        "app/model.py",
        "tests/test_main.py",
    ]

def test_read_files(tmp_path):
    workspace = tmp_path / "workspace"

    (workspace / "app").mkdir(parents=True)
    (workspace / "tests").mkdir(parents=True)

    main_content = "print('hello')\n"
    model_content = "class Model:\n    pass\n"
    test_content = "def test_model():\n    pass\n"

    (workspace / "app" / "main.py").write_text(main_content)
    (workspace / "app" / "model.py").write_text(model_content)
    (workspace / "tests" / "test_model.py").write_text(test_content)

    manager = WorkspaceManager(str(workspace))

    files = manager.read_files()

    assert files == {
        "app/main.py": main_content,
        "app/model.py": model_content,
        "tests/test_model.py": test_content,
    }

def test_write_files(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    manager = WorkspaceManager(str(workspace))

    files = {
        "app/main.py": "print('hello')\n",
        "app/model.py": "class Model:\n    pass\n",
        "tests/test_model.py": (
            "def test_model():\n"
            "    pass\n"
        ),
    }

    manager.write_files(files)

    assert (
        workspace / "app" / "main.py"
    ).read_text() == files["app/main.py"]

    assert (
        workspace / "app" / "model.py"
    ).read_text() == files["app/model.py"]

    assert (
        workspace / "tests" / "test_model.py"
    ).read_text() == files["tests/test_model.py"]

from textwrap import dedent

from services.codegen.app.schemas import FilePatch
from shared.workspace.manager import WorkspaceManager


def test_apply_patch_to_real_file(tmp_path):
    workspace = tmp_path / "workspace"

    app_dir = workspace / "app"
    app_dir.mkdir(parents=True)

    math_file = app_dir / "math_utils.py"

    original_content = (
        "def add(a, b):\n"
        "    return a + b\n"
    )

    math_file.write_text(original_content)

    manager = WorkspaceManager(str(workspace))

    patch = FilePatch(
        file_path="app/math_utils.py",
        patch=dedent("""\
            --- a/app/math_utils.py
            +++ b/app/math_utils.py
            @@ -1,2 +1,5 @@
             def add(a, b):
                 return a + b
            +
            +def multiply(a, b):
            +    return a * b
            """),
    )

    print("\n" + "=" * 60)
    print("FILE BEFORE PATCH")
    print("=" * 60)
    print(math_file.read_text())

    manager.apply_patch(patch)

    updated_content = math_file.read_text()

    print("=" * 60)
    print("FILE AFTER PATCH")
    print("=" * 60)
    print(updated_content)
    print("=" * 60)

    assert updated_content == (
        "def add(a, b):\n"
        "    return a + b\n"
        "\n"
        "def multiply(a, b):\n"
        "    return a * b\n"
    )

def test_read_selected_files(tmp_path):
    workspace = WorkspaceManager(str(tmp_path))

    workspace.write_file(
        "app/main.py",
        "print('main')"
    )

    workspace.write_file(
        "app/config.py",
        "DEBUG = True"
    )

    workspace.write_file(
        "app/utils.py",
        "def hello(): pass"
    )

    files = workspace.read_selected_files(
        [
            "app/main.py",
            "app/config.py",
        ]
    )

    assert files == {
        "app/main.py": "print('main')",
        "app/config.py": "DEBUG = True",
    }

    assert "app/utils.py" not in files

def test_read_selected_files_missing_file(tmp_path):
    workspace = WorkspaceManager(str(tmp_path))

    workspace.write_file(
        "app/main.py",
        "print('main')"
    )

    with pytest.raises(WorkspaceError, match="File not found"):
        workspace.read_selected_files(
            [
                "app/main.py",
                "app/missing.py",
            ]
        )

def test_context_retriever(tmp_path):
    workspace = WorkspaceManager(str(tmp_path))

    workspace.write_file(
        "app/main.py",
        "print('main')",
    )

    workspace.write_file(
        "app/config.py",
        "DEBUG = True",
    )

    retriever = ContextRetriever(workspace)

    context = retriever.retrieve(
        [
            "app/main.py",
        ]
    )

    assert context == {
        "app/main.py": "print('main')",
    }

def test_context_retriever_missing_file(tmp_path):
    workspace = WorkspaceManager(str(tmp_path))

    retriever = ContextRetriever(workspace)

    with pytest.raises(WorkspaceError):
        retriever.retrieve(
            ["app/missing.py"]
        )

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