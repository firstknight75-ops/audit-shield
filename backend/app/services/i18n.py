from __future__ import annotations

from app.i18n.translations import TRANSLATIONS


def tr(key: str, language: str = 'ar') -> str:
    table = TRANSLATIONS.get(key, {})
    return table.get(language) or table.get('ar') or key
