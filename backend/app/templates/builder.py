from __future__ import annotations

import json

SECTOR_PRESETS = {
    'Manufacturing': {'widgets': ['waste_map', 'risk_map', 'oee_loss']},
    'Restaurant': {'widgets': ['food_cost', 'waste_map', 'table_turnover']},
    'Real Estate': {'widgets': ['vacancy_rate', 'maintenance_margin', 'risk_map']},
    'Trading': {'widgets': ['inventory_turnover', 'gross_margin', 'waste_map']},
}


def build_template(name: str, sector: str, widgets: list[str]) -> str:
    return json.dumps({'name': name, 'sector': sector, 'widgets': widgets}, ensure_ascii=False)
