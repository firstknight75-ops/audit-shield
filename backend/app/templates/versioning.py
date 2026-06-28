from __future__ import annotations

import json


def bump_version(current: int) -> int:
    return current + 1


def rollback_payload(current_payload: str, previous_payload: str) -> str:
    json.loads(current_payload)
    json.loads(previous_payload)
    return previous_payload
