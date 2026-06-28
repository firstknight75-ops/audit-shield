from pydantic import BaseModel


class LedgerVerifyResponse(BaseModel):
    valid: bool
    message: str
    broken_entry_id: str | None = None
