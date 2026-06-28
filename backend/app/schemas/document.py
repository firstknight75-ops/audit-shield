from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    mime_type: str
    size: int
    encrypted: bool = True
