from textwrap import dedent

import pytest

from services.codegen.app.schemas import FilePatch
from shared.patches.applier import (
    PatchApplicationError,
    apply_patch,
)


def test_add_line():
    existing_files = {
        "app/math_utils.py": (
            "def add(a, b):\n"
            "    return a + b\n"
        )
    }

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

    updated_files = apply_patch(
        patch,
        existing_files,
    )

    assert updated_files["app/math_utils.py"] == (
        "def add(a, b):\n"
        "    return a + b\n"
        "\n"
        "def multiply(a, b):\n"
        "    return a * b\n"
    )


def test_delete_line():
    existing_files = {
        "app/math_utils.py": (
            "def add(a, b):\n"
            "    return a + b\n"
            "\n"
            "def multiply(a, b):\n"
            "    return a * b\n"
        )
    }

    patch = FilePatch(
        file_path="app/math_utils.py",
        patch=dedent("""\
            --- a/app/math_utils.py
            +++ b/app/math_utils.py
            @@ -1,5 +1,2 @@
             def add(a, b):
                 return a + b
            -
            -def multiply(a, b):
            -    return a * b
            """),
    )

    updated_files = apply_patch(
        patch,
        existing_files,
    )

    assert updated_files["app/math_utils.py"] == (
        "def add(a, b):\n"
        "    return a + b\n"
    )


def test_modify_line():
    existing_files = {
        "app/math_utils.py": (
            "def add(a, b):\n"
            "    return a + b\n"
        )
    }

    patch = FilePatch(
        file_path="app/math_utils.py",
        patch=dedent("""\
            --- a/app/math_utils.py
            +++ b/app/math_utils.py
            @@ -1,2 +1,2 @@
             def add(a, b):
            -    return a + b
            +    return a + b + 1
            """),
    )

    updated_files = apply_patch(
        patch,
        existing_files,
    )

    assert updated_files["app/math_utils.py"] == (
        "def add(a, b):\n"
        "    return a + b + 1\n"
    )


def test_reject_patch_when_context_does_not_match():
    existing_files = {
        "app/math_utils.py": (
            "def add(a, b):\n"
            "    return a + b + 100\n"
        )
    }

    patch = FilePatch(
        file_path="app/math_utils.py",
        patch=dedent("""\
            --- a/app/math_utils.py
            +++ b/app/math_utils.py
            @@ -1,2 +1,2 @@
             def add(a, b):
            -    return a + b
            +    return a + b + 1
            """),
    )

    with pytest.raises(PatchApplicationError):
        apply_patch(
            patch,
            existing_files,
        )


def test_original_files_are_not_modified():
    existing_files = {
        "app/math_utils.py": (
            "def add(a, b):\n"
            "    return a + b\n"
        )
    }

    original_content = existing_files["app/math_utils.py"]

    patch = FilePatch(
        file_path="app/math_utils.py",
        patch=dedent("""\
            --- a/app/math_utils.py
            +++ b/app/math_utils.py
            @@ -1,2 +1,2 @@
             def add(a, b):
            -    return a + b
            +    return a + b + 1
            """),
    )

    updated_files = apply_patch(
        patch,
        existing_files,
    )

    assert existing_files["app/math_utils.py"] == original_content

    assert updated_files["app/math_utils.py"] != original_content