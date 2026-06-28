from pydantic import BaseModel


class CertificationField(BaseModel):
    key: str
    label: str
    value: str | list[str]
    confidence: int
    color: str
    requires_correction: bool


class CertificationNextResponse(BaseModel):
    document_id: str
    filename: str
    extraction_id: str
    fields: list[CertificationField]


class CertificationRequest(BaseModel):
    fields: dict[str, str | list[str]]


class OCRQueueResponse(BaseModel):
    document_id: str
    extraction_id: str
    status: str
