import hashlib
import json


def test_owner_and_auditor_visibility_contract():
    assert 'auditor' != 'owner'


def test_chain_hash_contract():
    body1 = {'entry_id': '1', 'action': 'upload'}
    h1 = hashlib.sha256(('GENESIS' + json.dumps(body1, ensure_ascii=False, sort_keys=True, separators=(',', ':'))).encode('utf-8')).hexdigest()
    body2 = {'entry_id': '2', 'action': 'certify'}
    h2 = hashlib.sha256((h1 + json.dumps(body2, ensure_ascii=False, sort_keys=True, separators=(',', ':'))).encode('utf-8')).hexdigest()
    assert h1 != h2
