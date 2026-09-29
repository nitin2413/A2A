from pydantic import BaseModel

class FilePatch(BaseModel):
    ...

class CodegenResponse(BaseModel):
    summary : str
    files : dict[str , str]
    tests : list[str]