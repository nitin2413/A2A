from pydantic import BaseModel , Field

class FilePatch(BaseModel):
    file_path: str
    patch: str


class CodegenResponse(BaseModel):
    summary: str
    patches: list[FilePatch]