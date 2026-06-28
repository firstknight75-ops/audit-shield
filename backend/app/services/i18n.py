from __future__ import annotations

from app.i18n.translations import TRANSLATIONS


def tr(key: str, language: str = 'ar') -> str:
    """Translate a key to the given language.

    Falls back through: requested language → Arabic → raw key.
    Runtime DB lookup will override the in-memory dict when the
    Translation table is seeded, but the in-memory dict remains the
    primary source at import-time.
    """
    table = TRANSLATIONS.get(key, {})
    return table.get(language) or table.get('ar') or key
