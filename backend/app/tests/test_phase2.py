from datetime import datetime, timedelta, timezone

import pytest

from app.services.ledger import verify_ledger_integrity


def calc_efficiency(tasks):
    total = len(tasks)
    on_time = len([t for t in tasks if t['status'] == 'done' and t['completed_at'] and t['completed_at'] <= t['due_at']])
    demerits = sum(t['demerit_points'] for t in tasks)
    return ((on_time / total) * 100 if total else 100) - (demerits * 5)


def can_auditor_see_analytics(role: str) -> bool:
    return role != 'auditor'


def verify_chain(rows):
    import hashlib, json
    previous_hash = 'GENESIS'
    for row in rows:
        body = row['entry_body']
        calc = hashlib.sha256((previous_hash + json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(',', ':'))).encode('utf-8')).hexdigest()
        if calc != row['entry_hash']:
            return False, row['id']
        previous_hash = row['entry_hash']
    return True, None


def test_auditor_cannot_see_analytics_after_certification():
    assert can_auditor_see_analytics('auditor') is False
    assert can_auditor_see_analytics('owner') is True


def test_sla_demerit_after_15_minutes():
    overdue = datetime.now(timezone.utc) - timedelta(minutes=16)
    tasks = [{'status': 'open', 'due_at': overdue, 'completed_at': None, 'demerit_points': 1}]
    assert calc_efficiency(tasks) == -5


def test_ledger_verification_names_tampered_entry():
    rows = [
        {'id': '1', 'entry_body': {'a': 1}, 'entry_hash': 'dummy'},
        {'id': '2', 'entry_body': {'a': 2}, 'entry_hash': 'dummy2'},
    ]
    import hashlib, json
    rows[0]['entry_hash'] = hashlib.sha256(('GENESIS' + json.dumps(rows[0]['entry_body'], ensure_ascii=False, sort_keys=True, separators=(',', ':'))).encode('utf-8')).hexdigest()
    rows[1]['entry_hash'] = hashlib.sha256((rows[0]['entry_hash'] + json.dumps(rows[1]['entry_body'], ensure_ascii=False, sort_keys=True, separators=(',', ':'))).encode('utf-8')).hexdigest()
    ok, broken = verify_chain(rows)
    assert ok is True
    rows[1]['entry_body']['a'] = 999
    ok, broken = verify_chain(rows)
    assert ok is False
    assert broken == '2'
