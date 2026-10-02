import pytest

from services.codegen.app.schemas import FilePatch
from shared.patches.validator import (
    PatchValidationError,
    validate_patch,
)


def test_valid_patch():
    patch = FilePatch(
        file_path="app/math_utils.py",
        patch="""--- a/app/math_utils.py
+++ b/app/math_utils.py
@@
 def add(a, b):
     return a + b
""",
    )

    existing_files = {
        "app/math_utils.py": "def add(a, b):\n    return a + b\n"
    }

    validate_patch(patch, existing_files)


def test_reject_absolute_path():
    patch = FilePatch(
        file_path="/etc/passwd",
        patch="some patch",
    )

    with pytest.raises(PatchValidationError):
        validate_patch(patch, {})


def test_reject_path_traversal():
    patch = FilePatch(
        file_path="../secret.py",
        patch="some patch",
    )

    with pytest.raises(PatchValidationError):
        validate_patch(patch, {})


def test_reject_unknown_file():
    patch = FilePatch(
        file_path="app/unknown.py",
        patch="some patch",
    )

    existing_files = {
        "app/main.py": "print('hello')"
    }

    with pytest.raises(PatchValidationError):
        validate_patch(patch, existing_files)


def test_reject_empty_patch():
    patch = FilePatch(
        file_path="app/main.py",
        patch="",
    )

    existing_files = {
        "app/main.py": "print('hello')"
    }

    with pytest.raises(PatchValidationError):
        validate_patch(patch, existing_files)