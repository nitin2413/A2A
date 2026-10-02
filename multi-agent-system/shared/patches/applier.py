from unidiff import PatchSet

from services.codegen.app.schemas import FilePatch
from shared.patches.validator import validate_patch


class PatchApplicationError(Exception):
    pass


def apply_patch(
    patch: FilePatch,
    existing_files: dict[str, str],
) -> dict[str, str]:
    """
    Apply a unified diff to one file.

    Returns a new dictionary containing the modified file contents.
    The original existing_files dictionary is not modified.
    """

    # ---------------------------------------------------------
    # 1. Basic validation
    # ---------------------------------------------------------
    validate_patch(patch, existing_files)

    file_path = patch.file_path
    current_file = existing_files[file_path]

    # ---------------------------------------------------------
    # 2. Parse the unified diff
    # ---------------------------------------------------------
    try:
        patch_set = PatchSet(patch.patch)
    except Exception as exc:
        raise PatchApplicationError(
            f"Invalid unified diff for {file_path}: {exc}"
        ) from exc

    # A FilePatch should describe exactly one file.
    if len(patch_set) != 1:
        raise PatchApplicationError(
            f"Expected patch for exactly one file, "
            f"got {len(patch_set)}."
        )

    patched_file = patch_set[0]

    # ---------------------------------------------------------
    # 3. Make sure the diff targets the expected file
    # ---------------------------------------------------------
    patch_path = patched_file.path

    if patch_path.startswith("a/"):
        patch_path = patch_path[2::]
    if patch_path.startswith("b/"):
        patch_path = patch_path[2::]
    if patch_path != file_path:
        raise PatchApplicationError(
            f"Patch targets '{patch_path}', "
            f"but FilePatch targets '{file_path}'."
        )

    # ---------------------------------------------------------
    # 4. Split current file into lines
    # ---------------------------------------------------------
    current_lines = current_file.splitlines(keepends=True)
    new_lines: list[str] = []
    current_index = 0

    # ---------------------------------------------------------
    # 5. Apply each hunk
    # ---------------------------------------------------------
    for hunk in patched_file:
        hunk_start = hunk.source_start - 1 # python start from 0 and hunk from 1
        if hunk_start < current_index:
            raise PatchApplicationError(
                f"Overlapping or incorrectly ordered hunks "
                f"in patch for {file_path}."
            )

        new_lines.extend(current_lines[current_index:hunk_start]) # append the parts, where we dont need to change code

        current_index = hunk_start
        # -----------------------------------------------------
        # Process lines inside the hunk
        # -----------------------------------------------------
        for line in hunk:
            if line.line_type == " ":# start with space get append in new_file from old file
                if current_index >= len(current_lines): # current_idx == 0 and len() -> number of line in current_line
                    raise PatchApplicationError(
                        f"Patch context goes beyond the end of "
                        f"{file_path}."
                    )
                expected = line.value
                actual = current_lines[current_index]

                if actual != expected:
                    raise PatchApplicationError(
                        f"Patch context does not match "
                        f"{file_path} at line "
                        f"{current_index + 1}.\n"
                        f"Expected: {expected!r}\n"
                        f"Actual:   {actual!r}"
                    )
                new_lines.append(actual)
                current_index += 1

            elif line.line_type == "-": # we skip the line which we do not want from old file
                if current_index >= len(current_lines):
                    raise PatchApplicationError(
                        f"Patch tries to delete beyond the end "
                        f"of {file_path}."
                    )
                expected = line.value
                actual = current_lines[current_index]

                if actual != expected:
                    raise PatchApplicationError(
                        f"Patch deletion does not match "
                        f"{file_path} at line "
                        f"{current_index + 1}.\n"
                        f"Expected: {expected!r}\n"
                        f"Actual:   {actual!r}"
                    )
                current_index += 1 # do not append unwanted lines start with -

            # Added line:
            # It does not consume anything from the old file.
            elif line.line_type == "+":
                new_lines.append(line.value)

                # Ignore special unified-diff metadata such as:
                # "\ No newline at end of file"
            elif line.line_type == "\\":
                continue

            else:
                raise PatchApplicationError(
                    f"Unknown diff line type: "
                    f"{line.line_type!r}"
                )


    # ---------------------------------------------------------
    # 6. Copy everything after the final hunk
    # ---------------------------------------------------------
    new_lines.extend(current_lines[current_index:])

    updated_file = "".join(new_lines)

    # ---------------------------------------------------------
    # 7. Return a NEW dictionary
    # ---------------------------------------------------------
    updated_files = existing_files.copy()
    updated_files[file_path] = updated_file

    return updated_files


