from services.codegen.app.schemas import FilePatch
from shared.patches.applier import apply_patch
from shared.workspace.manager import WorkspaceManager

class PatchManagerError(Exception):
    pass

class PatchManager():
    def __init__(self , workspace:WorkspaceManager):
        self.workspace = workspace

    def apply_patches(self, patches : list[FilePatch])->list[str]:
        file_paths = [patch.file_path for patch in patches]
        existing_files = self.workspace.read_selected_files(file_paths)
        updated_files = existing_files.copy()
        try:
            for patch in patches:
                updated_files = apply_patch(
                    patch,
                    updated_files,
                )

        except Exception as exc:
            raise PatchManagerError(
                f"Failed to apply patches: {exc}"
            ) from exc

        changed_files = {
            path : content
            for path , content in updated_files.items()
            if content != existing_files[path]
        }
        self.workspace.write_files(changed_files)
        return list(changed_files.keys())
