import pytest

from services.codegen.app.schemas import FilePatch
from shared.patches.manager import PatchManager, PatchManagerError
from shared.workspace.manager import WorkspaceManager


def test_patch_manager_does_not_partially_apply(
    tmp_path,
):
    workspace = WorkspaceManager(str(tmp_path))

    workspace.write_file(
        "app/a.py",
        """def a():
    return 1
""",
    )

    workspace.write_file(
        "app/b.py",
        """def b():
    return 2
""",
    )

    manager = PatchManager(workspace)

    valid_patch = FilePatch(
        file_path="app/a.py",
        patch="""--- a/app/a.py
+++ b/app/a.py
@@ -1,2 +1,5 @@
 def a():
     return 1
+
+
+def new_a():
+    return 10
""",
    )

    invalid_patch = FilePatch(
        file_path="app/b.py",
        patch="""--- a/app/b.py
+++ b/app/b.py
@@ -1,2 +1,5 @@
 def b():
-    return WRONG
+    return 20
""",
    )

    with pytest.raises(PatchManagerError):
        manager.apply_patches(
            [valid_patch, invalid_patch]
        )

    assert workspace.read_file("app/a.py") == """def a():
    return 1
"""

    assert workspace.read_file("app/b.py") == """def b():
    return 2
"""