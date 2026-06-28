from pydantic import BaseModel


class ExportRequest(BaseModel):
    output_code: str
    format: str


class WhatIfRequest(BaseModel):
    waste_map_item_id: str
    recovery_percent: float
    implementation_months: int
    manual_cost: float
    horizon_months: int = 6


class ClientInventoryResponse(BaseModel):
    id: str
    name: str
    sector: str
    tier: str
    deployment_mode: str
    user_count: int
    user_cap: int
    last_health_check: str | None = None
    last_backup: str | None = None
