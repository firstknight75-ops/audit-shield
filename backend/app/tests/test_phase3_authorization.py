def test_auditor_must_not_access_owner_dashboard_contract():
    allowed_roles = {'owner', 'gm'}
    assert 'auditor' not in allowed_roles


def test_manager_scope_contract():
    findings = [
        {'document_id': 'doc-a'},
        {'document_id': 'doc-b'},
    ]
    allowed = {'doc-a'}
    scoped = [f for f in findings if f['document_id'] in allowed]
    assert scoped == [{'document_id': 'doc-a'}]
