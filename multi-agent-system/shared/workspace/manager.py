from pathlib import Path
from services.codegen.app.schemas import FilePatch
from shared.patches.applier import apply_patch as apply_file_patch

class WorkspaceError(Exception):
    pass

class WorkspaceManager():
    def __init__(self , root):
        self.root = Path(root) # change from root because _resolve_path() assumes it's a Path.

    def _resolve_path(self,file_path : str)->Path:
        root = self.root.resolve()
        target = (self.root / file_path).resolve()
        if target.is_relative_to(root):
            return target
        else:
            raise WorkspaceError(
                f"Path escapes workspace: {file_path}"
            )

    def read_file(self , file_path: str)->str:
        try:
            full_path = self._resolve_path(file_path)

            with open(full_path, "r") as f:
                content = f.read()
            return content
        except FileNotFoundError as exc:
            raise WorkspaceError(
                f"File not found: {file_path}"
            ) from exc

        except PermissionError as exc:
            raise WorkspaceError(
                f"Permission denied: {file_path}"
            ) from exc

        except OSError as exc:
            raise WorkspaceError(
                f"Could not read file '{file_path}': {exc}"
            ) from exc

    def write_file(self, file_path: str , content: str)->None:
        try:
            full_path = self._resolve_path(file_path)
            #exist_ok=True means:  if the directory already exists, don't raise an error.
            full_path.parent.mkdir(parents=True , exist_ok=True) # check the existence of parent directly if not then create them
            with open(full_path , "w") as f:
                f.write(content)
        except PermissionError as exc:
            raise WorkspaceError(
                f"Permission denied: {file_path}"
            ) from exc

        except OSError as exc:
            raise WorkspaceError(
                f"Could not write file '{file_path}': {exc}"
            ) from exc

    def list_files(self)->list[str]:
        ignored_directories = {
            ".git",
            ".venv",
            "__pycache__"
            ".pytest_cache"
        }
        files:list[str] = []
        try:
            for path in self.root.rglob("*"):
                if not path.is_file():
                    continue

                if any(
                    part in ignored_directories
                    for part in path.relative_to(self.root).parts
                ):
                    continue

                if path.suffix == ".pyc":
                    continue

                relative_path = path.relative_to(self.root)

                files.append(str(relative_path))

            return sorted(files)

        except PermissionError as exc:
            raise WorkspaceError(
                f"Permission denied while listing workspace: "
                f"{self.root}"
            ) from exc

        except OSError as exc:
            raise WorkspaceError(
                f"Could not list workspace '{self.root}': {exc}"
            ) from exc

    def read_files(self)->dict[str , str]:
        try:
            work_files = self.list_files()
            data : dict[str , str] = {}
            for file in work_files:
                content = self.read_file(file)
                data[file] = content
            return data
        except WorkspaceError:
            # Preserve the more specific error from read_file()
            raise

        except OSError as exc:
            raise WorkspaceError(
                f"Could not read workspace files: {exc}"
            ) from exc

    def write_files(self , files : dict[str, str])->None:
        for file_path , content in files.items():
            self.write_file(file_path , content)

    def apply_patch(self , patch:FilePatch)->None:
        existing_file = self.read_files()
        update_file = apply_file_patch(patch,existing_file)
        updated_content = update_file[patch.file_path]
        self.write_file(
            patch.file_path,
            updated_content,
        )

    def read_selected_files(self,file_paths: list[str]) -> dict[str, str]:
        data: dict[str, str] = {}

        for file_path in file_paths:
            data[file_path] = self.read_file(file_path)

        return data