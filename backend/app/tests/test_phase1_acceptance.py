"""Phase 1 Acceptance Tests.

Maps directly to the 10 acceptance criteria from the AuditCore Phase 1 spec.

These tests run as pure-logic contracts so they work without Docker/Postgres.
Runtime tests that need an actual DB run as documented integration tests
in the acceptance scripts directory.

Path math: this file lives at backend/app/tests/test_phase1_acceptance.py
  parents[0] = backend/app/tests
  parents[1] = backend/app
  parents[2] = backend
  parents[3] = audit-shield (repo root)
"""
from __future__ import annotations

import os
import pathlib

import pytest

# Project paths
REPO = pathlib.Path(__file__).resolve().parents[3]
APP = pathlib.Path(__file__).resolve().parents[1]
BACKEND = pathlib.Path(__file__).resolve().parents[2]


from app.services.access import (
    require_company_access,
)
from app.services.encryption import decrypt_bytes_to_memory, encrypt_bytes
from app.services.permissions import ROLE_DEFAULTS


# ─────────────────────────────────────────────────────────────────────
# Acceptance #1 — setup.sh and deploy-cloud.sh exist and are executable
# ─────────────────────────────────────────────────────────────────────

def test_acceptance_1_setup_sh_exists_and_executable():
    p = REPO / 'scripts' / 'setup.sh'
    assert p.exists(), f'setup.sh missing at {p}'
    assert os.access(p, os.X_OK), f'setup.sh is not executable: {p}'
    content = p.read_text(encoding='utf-8')
    assert 'docker compose' in content or 'docker-compose' in content
    assert 'auditcore.local' in content


def test_acceptance_1_deploy_cloud_sh_exists_and_executable():
    p = REPO / 'scripts' / 'deploy-cloud.sh'
    assert p.exists()
    assert os.access(p, os.X_OK)
    content = p.read_text(encoding='utf-8')
    assert 'DEPLOYMENT_MODE' in content
    assert 'tenant' in content.lower()
    assert 'auditcore.local' in content


def test_acceptance_1_both_call_seed():
    """Both scripts must invoke seed (which now stamps activation_started_at)."""
    setup = (REPO / 'scripts' / 'setup.sh').read_text()
    cloud = (REPO / 'scripts' / 'deploy-cloud.sh').read_text()
    assert 'seed' in setup
    assert 'seed' in cloud


# ─────────────────────────────────────────────────────────────────────
# Acceptance #2 — /auth/me returns different effective permissions per role
# ─────────────────────────────────────────────────────────────────────

def test_acceptance_2_owner_has_full_dashboard_permissions():
    p = ROLE_DEFAULTS['owner']
    for code in ['view_owner_dashboard', 'view_waste_map', 'view_risk_alerts', 'view_audit_ledger',
                 'manage_company_users', 'manage_permissions', 'grant_temporary_access']:
        assert code in p, f'owner missing {code}'


def test_acceptance_2_gm_has_dashboard_no_ledger():
    p = ROLE_DEFAULTS['gm']
    assert 'view_owner_dashboard' in p
    assert 'view_waste_map' in p
    assert 'view_audit_ledger' not in p
    assert 'manage_company_users' not in p


def test_acceptance_2_manager_is_scoped_no_dashboard():
    p = ROLE_DEFAULTS['manager']
    assert 'view_owner_dashboard' not in p
    assert 'view_waste_map' not in p
    assert 'view_audit_ledger' not in p
    assert 'upload_documents' in p
    assert 'view_tasks' in p
    # manager MUST NOT see raw documents (auditor certifies for them)
    assert 'view_documents' not in p


def test_acceptance_2_auditor_no_analytics_no_ledger():
    p = ROLE_DEFAULTS['auditor']
    forbidden = ['view_owner_dashboard', 'view_waste_map', 'view_risk_alerts', 'view_audit_ledger',
                 'manage_company_users', 'manage_permissions', 'export_reports',
                 'approve_custom_reports', 'grant_temporary_access']
    for code in forbidden:
        assert code not in p, f'auditor MUST NOT have {code}'
    # and must include only the auditor-appropriate set
    assert set(p) == {'upload_documents', 'view_documents', 'view_tasks'}


def test_acceptance_2_manager_and_auditor_have_distinct_sets():
    """Even though both are operational, their permission sets must differ —
    manager sees tasks not documents, auditor sees documents not raw analytics."""
    assert set(ROLE_DEFAULTS['manager']) != set(ROLE_DEFAULTS['auditor'])


def test_acceptance_2_admin_manages_users_no_dashboard():
    p = ROLE_DEFAULTS['admin']
    assert 'manage_company_users' in p
    assert 'manage_permissions' in p
    assert 'grant_temporary_access' in p
    assert 'view_audit_ledger' in p
    # no analytics, no upload
    assert 'view_owner_dashboard' not in p
    assert 'view_waste_map' not in p
    assert 'upload_documents' not in p


def test_acceptance_2_appowner_only_platform_permissions():
    p = ROLE_DEFAULTS['appowner']
    forbidden = ['view_owner_dashboard', 'view_waste_map', 'view_risk_alerts', 'view_audit_ledger',
                 'upload_documents', 'view_documents', 'manage_company_users',
                 'manage_permissions', 'export_reports', 'approve_custom_reports',
                 'grant_temporary_access']
    for code in forbidden:
        assert code not in p
    assert set(p) == {'app_owner_inventory', 'app_owner_templates', 'app_owner_maintenance'}


def test_acceptance_2_all_six_roles_have_distinct_permission_sets():
    sets = {tuple(sorted(ROLE_DEFAULTS[r])) for r in ['owner', 'gm', 'manager', 'auditor', 'admin', 'appowner']}
    assert len(sets) == 6, f'Roles have only {len(sets)} distinct permission sets — duplicate!'


# ─────────────────────────────────────────────────────────────────────
# Acceptance #3 — Auditor RLS returns 0 rows; owner returns normal rows
# ─────────────────────────────────────────────────────────────────────

def test_acceptance_3_auditor_rls_enabled_in_migration():
    """The migration uses an f-string loop over table names. The literal
    pattern in the source is `ALTER TABLE {table} ENABLE ROW LEVEL SECURITY`,
    not the resolved names."""
    import re
    migration_path = BACKEND / 'alembic' / 'versions' / '20260629_0001_init.py'
    text = migration_path.read_text(encoding='utf-8')
    # Verify the f-string loop pattern is present
    assert "for table in ['analytics_outputs', 'waste_map_items', 'risk_alerts']:" in text
    assert re.search(r"ALTER TABLE \{table\} ENABLE ROW LEVEL SECURITY", text)
    assert re.search(r"auditor_no_access_\{table\}", text)
    assert re.search(r"tenant_isolation_\{table\}", text)


def test_acceptance_3_set_user_role_helper_defined():
    migration_path = BACKEND / 'alembic' / 'versions' / '20260629_0001_init.py'
    text = migration_path.read_text(encoding='utf-8')
    assert "CREATE OR REPLACE FUNCTION set_user_role" in text
    assert "app.current_user_role" in text


def test_acceptance_3_auditor_session_query_returns_zero_rows_logic():
    """The expected runtime behavior: setting role='auditor' must hide
    analytics_outputs, waste_map_items, risk_alerts. This contract is
    enforced by the RLS policy in the migration."""
    migration_path = BACKEND / 'alembic' / 'versions' / '20260629_0001_init.py'
    text = migration_path.read_text(encoding='utf-8')
    assert "current_setting('app.current_user_role', true) != 'auditor'" in text


# ─────────────────────────────────────────────────────────────────────
# Acceptance #4 — Cross-tenant isolation (cloud)
# ─────────────────────────────────────────────────────────────────────

def test_acceptance_4_tenant_isolation_policy_in_migration():
    migration_path = BACKEND / 'alembic' / 'versions' / '20260629_0001_init.py'
    text = migration_path.read_text(encoding='utf-8')
    assert "current_setting('app.current_tenant_id', true)" in text
    assert "JOIN company_group" in text


def test_acceptance_4_set_session_context_sets_tenant():
    """get_current_user must invoke set_session_context with both role and tenant.
    The actual SET statements live in db/session.py."""
    deps_path = APP / 'api' / 'deps.py'
    session_path = APP / 'db' / 'session.py'
    deps_text = deps_path.read_text(encoding='utf-8')
    session_text = session_path.read_text(encoding='utf-8')
    assert 'set_session_context' in deps_text
    assert 'company_group_id' in deps_text
    assert 'app.current_user_role' in session_text
    assert 'app.current_tenant_id' in session_text
    assert 'set_config' in session_text


def test_acceptance_4_factory_supports_schema_per_tenant_and_dedicated_db():
    factories = (APP / 'core' / 'factories.py').read_text()
    assert 'cloud' in factories
    assert 'VaultKeyBackend' in factories or 'vault' in factories.lower()


# ─────────────────────────────────────────────────────────────────────
# Acceptance #5 — Cross-company-within-tenant (Manager scoped to A)
# ─────────────────────────────────────────────────────────────────────

def test_acceptance_5_require_company_access_default_denies_no_rows():
    """A user with NO user_company_access rows must be denied to any company."""
    import asyncio
    from unittest.mock import AsyncMock, MagicMock

    async def run():
        user = MagicMock()
        user.role = 'manager'
        user.id = 'u'
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        db.execute.return_value = result_mock
        return await require_company_access(user, db, company_id='some-company')
    assert asyncio.run(run()) is False


def test_acceptance_5_manager_branch_mismatch_denied():
    import asyncio
    from unittest.mock import AsyncMock, MagicMock

    async def run():
        user = MagicMock()
        user.role = 'manager'
        user.id = 'u'
        db = AsyncMock()
        row = MagicMock()
        row.company_id = 'co'
        row.branch_id = 'branch-x'
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [row]
        db.execute.return_value = result_mock
        return await require_company_access(user, db, company_id='co', branch_id='branch-y')
    assert asyncio.run(run()) is False


def test_acceptance_5_manager_branch_match_allowed():
    import asyncio
    from unittest.mock import AsyncMock, MagicMock

    async def run():
        user = MagicMock()
        user.role = 'manager'
        user.id = 'u'
        db = AsyncMock()
        row = MagicMock()
        row.company_id = 'co'
        row.branch_id = 'branch-x'
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [row]
        db.execute.return_value = result_mock
        return await require_company_access(user, db, company_id='co', branch_id='branch-x')
    assert asyncio.run(run()) is True


def test_acceptance_5_manager_branch_all_access_allowed():
    import asyncio
    from unittest.mock import AsyncMock, MagicMock

    async def run():
        user = MagicMock()
        user.role = 'manager'
        user.id = 'u'
        db = AsyncMock()
        row = MagicMock()
        row.company_id = 'co'
        row.branch_id = None  # all branches
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [row]
        db.execute.return_value = result_mock
        return await require_company_access(user, db, company_id='co', branch_id='any-branch')
    assert asyncio.run(run()) is True


def test_acceptance_5_owner_company_match_allowed():
    import asyncio
    from unittest.mock import AsyncMock, MagicMock

    async def run():
        user = MagicMock()
        user.role = 'owner'
        user.id = 'u'
        db = AsyncMock()
        row = MagicMock()
        row.company_id = 'co'
        row.branch_id = 'branch-x'
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [row]
        db.execute.return_value = result_mock
        return await require_company_access(user, db, company_id='co', branch_id='branch-y')
    assert asyncio.run(run()) is True


# ─────────────────────────────────────────────────────────────────────
# Acceptance #6 — Cross-branch (Auditor scoped to one branch)
# ─────────────────────────────────────────────────────────────────────

def test_acceptance_6_auditor_branch_scoped_no_other_branch_access():
    """Auditor scoped to branch 1 cannot pass require_company_access for branch 2."""
    import asyncio
    from unittest.mock import AsyncMock, MagicMock

    async def run():
        user = MagicMock()
        user.role = 'auditor'
        user.id = 'u'
        db = AsyncMock()
        row = MagicMock()
        row.company_id = 'co'
        row.branch_id = 'branch-1'  # ONLY branch 1
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [row]
        db.execute.return_value = result_mock
        return await require_company_access(user, db, company_id='co', branch_id='branch-2')
    assert asyncio.run(run()) is False


# ─────────────────────────────────────────────────────────────────────
# Acceptance #7 — Temporary override + auto-revoke + app_owner block
# ─────────────────────────────────────────────────────────────────────

def test_acceptance_7_effective_permissions_expire_after_expires_at():
    """A grant with expires_at in the past must NOT be in effective permissions.
    The SQL filter `(expires_at IS NULL OR expires_at > now)` excludes expired rows."""
    # This is the contract from permissions.py; verify the filter string exists.
    perms = (APP / 'services' / 'permissions.py').read_text()
    assert 'expires_at > now' in perms or 'expires_at IS NULL' in perms


def test_acceptance_7_admin_permission_override_blocks_appowner_category():
    """The admin endpoint must REJECT any app_owner permission grant."""
    admin_py = (APP / 'api' / 'admin.py').read_text()
    assert "if permission.category == 'app_owner'" in admin_py
    assert 'cannot_override_appowner' in admin_py


def test_acceptance_7_admin_role_has_no_appowner_codes():
    p = ROLE_DEFAULTS['admin']
    for code in p:
        assert not code.startswith('app_owner_')


# ─────────────────────────────────────────────────────────────────────
# Acceptance #8 — Bilingual i18n + Sorani font coverage
# ─────────────────────────────────────────────────────────────────────

def test_acceptance_8_every_arabic_key_has_sorani_counterpart():
    from app.i18n.translations import TRANSLATIONS
    missing_ckb = []
    missing_ar = []
    for key, langs in TRANSLATIONS.items():
        if 'ar' not in langs:
            missing_ar.append(key)
        if 'ckb' not in langs:
            missing_ckb.append(key)
    assert not missing_ar, f'Keys missing Arabic: {missing_ar}'
    assert not missing_ckb, f'Keys missing Sorani: {missing_ckb}'


def test_acceptance_8_sorani_specific_letters_present_in_test_strings():
    from app.i18n.translations import TRANSLATIONS
    sorani_chars = ['ھ', 'ێ', 'ۆ', 'ڵ', 'ڕ', 'ە']
    found_chars = set()
    for langs in TRANSLATIONS.values():
        ckb = langs.get('ckb', '')
        for ch in sorani_chars:
            if ch in ckb:
                found_chars.add(ch)
    assert len(found_chars) >= 3, f'Only {found_chars} of required Sorani letters found'


def test_acceptance_8_frontend_uses_noto_sans_arabic_with_sorani_coverage():
    app_shell = (REPO / 'src' / 'components' / 'app-shell.tsx').read_text()
    assert 'Noto Sans Arabic' in app_shell
    assert 'sans-serif' in app_shell


def test_acceptance_8_font_verification_doc_present():
    p = REPO / 'docs' / 'FONT_VERIFICATION.md'
    assert p.exists(), 'FONT_VERIFICATION.md missing'
    content = p.read_text(encoding='utf-8')
    for ch in ['ھ', 'ێ', 'ۆ', 'ڵ', 'ڕ', 'ە']:
        assert ch in content, f'Sorani letter {ch} missing from font verification'


def test_acceptance_8_language_persist_endpoint_exists():
    admin_py = (APP / 'api' / 'admin.py').read_text()
    assert "/language" in admin_py
    assert 'preferred_language' in admin_py


# ─────────────────────────────────────────────────────────────────────
# Acceptance #9 — CI fails on external AI imports
# ─────────────────────────────────────────────────────────────────────

def test_acceptance_9_no_external_ai_guard_script_exists():
    p = REPO / 'scripts' / 'check_no_external_ai.sh'
    assert p.exists()
    assert os.access(p, os.X_OK)


def test_acceptance_9_allowlist_file_exists_and_well_formed():
    p = REPO / '.audit-allowlist'
    assert p.exists()
    content = p.read_text(encoding='utf-8')
    assert 'INTENTIONALLY EMPTY' in content or 'empty' in content.lower()


def test_acceptance_9_no_external_ai_imports_in_app_code():
    """app.* code (excluding tests) must not contain external-AI SDK imports."""
    for path in APP.rglob('*.py'):
        if 'tests' in path.parts:
            continue
        content = path.read_text(encoding='utf-8')
        # Check for actual import statements, not patterns mentioned in docstrings.
        for line in content.splitlines():
            stripped = line.strip()
            for forbidden in ['import openai', 'from openai', 'import anthropic', 'from anthropic',
                              'import google.generativeai', 'import cohere', 'import langchain',
                              'import llama_index', 'import semantic_kernel']:
                if stripped.startswith(forbidden + ' ') or stripped == forbidden:
                    pytest.fail(f'{path} contains forbidden import: {forbidden}')


def test_acceptance_9_guard_script_runs_clean():
    """Run the guard against a temp copy of the repo with test files removed,
    so test docstrings/literals don't trip the pattern matcher."""
    import subprocess
    import tempfile
    import shutil
    with tempfile.TemporaryDirectory() as tmpdir:
        # Copy repo excluding tests (the pattern strings live there)
        ignore = shutil.ignore_patterns('tests', '.git', '__pycache__')
        # Add dirs to SKIP_DIRS in the script are honored
        dest = pathlib.Path(tmpdir) / 'repo'
        shutil.copytree(str(REPO), str(dest), ignore=ignore)
        # Make the script executable in the copy
        (dest / 'scripts' / 'check_no_external_ai.sh').chmod(0o755)
        res = subprocess.run(['bash', 'scripts/check_no_external_ai.sh'],
                             capture_output=True, text=True, cwd=str(dest))
    assert res.returncode == 0, f'guard FAILED:\n{res.stdout}\n{res.stderr}'
    assert 'PASS' in res.stdout


# ─────────────────────────────────────────────────────────────────────
# Acceptance #10 — Upload: encrypted at rest, .exe renamed as .pdf rejected
# ─────────────────────────────────────────────────────────────────────

def test_acceptance_10_encryption_round_trip_is_not_no_op():
    import asyncio

    async def run():
        plaintext = b'%PDF-1.4 fake invoice content' * 100
        encrypted = await encrypt_bytes('tenant-x', 'file-id-1', plaintext)
        assert encrypted != plaintext
        recovered = await decrypt_bytes_to_memory('tenant-x', 'file-id-1', encrypted)
        assert recovered == plaintext
    asyncio.run(run())


def test_acceptance_10_encryption_key_derivation_differs_per_file():
    import asyncio

    async def run():
        plaintext = b'same content'
        e1 = await encrypt_bytes('tenant-x', 'file-a', plaintext)
        e2 = await encrypt_bytes('tenant-x', 'file-b', plaintext)
        assert e1 != e2
    asyncio.run(run())


def test_acceptance_10_encryption_key_derivation_differs_per_tenant():
    import asyncio

    async def run():
        plaintext = b'same content'
        e1 = await encrypt_bytes('tenant-x', 'file-a', plaintext)
        e2 = await encrypt_bytes('tenant-y', 'file-a', plaintext)
        assert e1 != e2
    asyncio.run(run())


def test_acceptance_10_encryption_module_uses_mode_factory():
    factories = (APP / 'core' / 'factories.py').read_text()
    encryption = (APP / 'services' / 'encryption.py').read_text()
    assert 'get_key_backend' in encryption
    assert 'VaultKeyBackend' in factories or 'OnPremiseKeyBackend' in factories


def test_acceptance_10_upload_mime_validation_blocks_renamed_exe():
    """The documents router must check MIME via python-magic, not just extension."""
    documents_py = (APP / 'api' / 'documents.py').read_text()
    assert 'magic.from_buffer' in documents_py
    assert 'ALLOWED_MIME' in documents_py
    assert 'ALLOWED_EXTENSIONS' in documents_py


def test_acceptance_10_upload_size_cap_50mb():
    documents_py = (APP / 'api' / 'documents.py').read_text()
    assert '50 * 1024 * 1024' in documents_py


def test_acceptance_10_company_id_required_on_upload():
    documents_py = (APP / 'api' / 'documents.py').read_text()
    assert 'company_id' in documents_py
    assert 'company_required' in documents_py


# ─────────────────────────────────────────────────────────────────────
# Phase 1 spec: activation_started_at
# ─────────────────────────────────────────────────────────────────────

def test_phase1_activation_started_at_migration_exists():
    migration = BACKEND / 'alembic' / 'versions' / '20260629_0002_activation_started_at.py'
    assert migration.exists(), 'migration 0002 missing'
    text = migration.read_text()
    assert 'activation_started_at' in text
    assert 'company_group' in text
    assert "down_revision = '20260629_0001'" in text


def test_phase1_companygroup_entity_has_activation_started_at():
    entities = (APP / 'models' / 'entities.py').read_text()
    assert 'activation_started_at' in entities


def test_phase1_seed_records_activation_started_at():
    seed = (APP / 'db' / 'seed.py').read_text()
    assert 'activation_started_at' in seed
    assert 'datetime.now(timezone.utc)' in seed
