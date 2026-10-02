from pathlib import PurePosixPath

from services.codegen.app.schemas import FilePatch


class PatchValidationError(Exception):
    pass


def validate_patch(
    patch: FilePatch,
    existing_files: dict[str, str],
) -> None:
    if not patch.file_path.strip():
        raise PatchValidationError(
            "Patch file path cannot be empty."
        )

    path = PurePosixPath(patch.file_path)

    if path.is_absolute():
        raise PatchValidationError(
            f"Absolute paths are not allowed: {patch.file_path}"
        )

    if ".." in path.parts:
        raise PatchValidationError(
            f"Path traversal is not allowed: {patch.file_path}"
        )

    if patch.file_path not in existing_files:
        raise PatchValidationError(
            f"Patch targets a file that was not provided: "
            f"{patch.file_path}"
        )

    if not patch.patch.strip():
        raise PatchValidationError(
            f"Patch for {patch.file_path} is empty."
        )