from shared.workspace.manager import WorkspaceManager

class ContextRetriever:
    def __init__(self, workspace : WorkspaceManager):
        self.workspace = workspace

    def retrieve(self , file_paths : str)->dict[str , str]:
        return self.workspace.read_selected_files(file_paths)