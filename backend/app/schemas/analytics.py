from pydantic import BaseModel


class OwnerDashboardResponse(BaseModel):
    monthly_waste: float
    trust_index: int
    critical_alerts: int
    predicted_cash_outflow: float
    auditor_efficiency: float
    narrative: str
    department_breakdown: list[dict]
    findings: list[dict]


class RecordTraceResponse(BaseModel):
    document_id: str
    filename: str
    ledger: list[dict]
    extracted_data: dict
