from app.templates.versioning import bump_version, rollback_payload


def test_template_versioning_and_rollback():
    assert bump_version(1) == 2
    prev = '{"name":"Trading Pro","widgets":["waste_map"]}'
    cur = '{"name":"Trading Pro","widgets":["waste_map","risk_map"]}'
    assert rollback_payload(cur, prev) == prev


def test_appowner_boundary_contract():
    appowner_permissions = {'app_owner_inventory', 'app_owner_templates', 'app_owner_maintenance'}
    assert 'view_owner_dashboard' not in appowner_permissions
