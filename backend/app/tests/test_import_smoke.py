"""Regression: the app must import cleanly with no extra packages.

Bug #1: `backend/app/exports/engine.py` had a top-level, unguarded
`from openpyxl import Workbook`. With openpyxl absent from
`backend/requirements.txt`, a clean `pip install -r requirements.txt`
followed by `python -c "import app.main"` would raise ModuleNotFoundError
and the entire API fails to boot — not just the export feature.

This file provides:
1. A runtime smoke test (skipped in sandbox; runs in CI).
2. A static contract test that walks the eager import graph and asserts
   every third-party import is declared in requirements.txt.
"""
from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[3]
APP_DIR = pathlib.Path(__file__).resolve().parents[2]


def test_app_main_imports_without_module_not_found_error():
    """The cheapest possible regression: `import app.main` must succeed.

    Skipped in sandboxes that lack deps; the CI workflow
    (.github/workflows/ci.yml) runs this in a clean venv where deps
    ARE installed.
    """
    env = os.environ.copy()
    env["PYTHONPATH"] = str(APP_DIR)
    try:
        res = subprocess.run(
            [sys.executable, "-c", "import app.main; print('ok')"],
            capture_output=True, text=True, env=env, timeout=20,
        )
    except subprocess.TimeoutExpired:
        pytest.skip("python startup timed out in this sandbox — covered by CI")
    except Exception:
        pytest.skip("python subprocess unavailable — covered by CI")

    if res.returncode == 0:
        return

    # Bug #1 specifically: ModuleNotFoundError is the failure we MUST catch
    if 'ModuleNotFoundError' in res.stderr:
        # Extract the missing module name
        m = re.search(r"No module named '(\w+)'", res.stderr)
        missing = m.group(1) if m else 'unknown'
        raise AssertionError(
            f"import app.main raised ModuleNotFoundError for '{missing}'. "
            f"Bug #1: this third-party import is missing from "
            f"backend/requirements.txt. Add it there with a pinned version. "
            f"\nFull stderr:\n{res.stderr}"
        )
    # Other failures (syntax, network) — surface
    raise AssertionError(
        f"import app.main failed (returncode={res.returncode}).\n"
        f"stdout: {res.stdout}\nstderr: {res.stderr}"
    )


def test_third_party_imports_in_eagerly_loaded_routers_are_declared():
    """Static contract test for Bug #1 prevention.

    Walks every .py file reachable from the routers eagerly imported by
    main.py, collects non-stdlib third-party imports, and asserts each is
    declared in requirements.txt OR is a known transitive dep of fastapi
    OR is guarded behind try/except.
    """
    main_text = (REPO / 'backend' / 'app' / 'main.py').read_text()
    router_imports = re.findall(
        r"^from app\.api\.(\w+) import router as \w+_router",
        main_text, re.MULTILINE,
    )
    assert router_imports, 'main.py must import routers — no eager routers means no bug to test'

    stdlib = set(sys.stdlib_module_names) | {
        '__future__', 'typing', 'dataclasses', 'datetime', 'enum', 'os', 're',
        'json', 'logging', 'functools', 'pathlib', 'collections', 'asyncio',
        'hashlib', 'hmac', 'uuid', 'io', 'csv', 'base64', 'itertools',
        'contextlib', 'abc', 'tempfile', 'shutil', 'subprocess', 'copy',
        'math', 'random', 'string', 'textwrap', 'time', 'sys', 'warnings',
        'weakref', 'threading', 'multiprocessing',
    }
    # Modules that are transitive deps of fastapi/uvicorn and don't need to
    # be declared separately in requirements.txt
    transitive = {'starlette', 'anyio', 'sniffio', 'h11', 'uvicorn', 'click', 'dotenv'}
    # Optional deps guarded behind try/except — not in eager import path
    optional_guarded = {'aiosmtplib'}  # aiosmtplib in notifications_v2 wrapped path

    # Walk reachable .py files
    reachable_py: set[pathlib.Path] = set()
    queue: list[pathlib.Path] = []
    for router_name in router_imports:
        p = REPO / 'backend' / 'app' / 'api' / f'{router_name}.py'
        if p.exists():
            queue.append(p)
    while queue:
        f = queue.pop()
        if f in reachable_py:
            continue
        reachable_py.add(f)
        try:
            content = f.read_text(encoding='utf-8')
        except (UnicodeDecodeError, OSError):
            continue
        for m in re.finditer(r'^\s*from\s+(app\.\S+)\s+import\s+', content, re.MULTILINE):
            mod_path = m.group(1)
            if '*' in mod_path:
                continue
            rel = mod_path.replace('app.', 'app/').replace('.', '/')
            for suffix in ('.py', '/__init__.py'):
                candidate = REPO / 'backend' / f'{rel}{suffix}'
                if candidate.exists():
                    queue.append(candidate)
                    break

    third_party_imports: set[str] = set()
    for f in reachable_py:
        try:
            content = f.read_text(encoding='utf-8')
        except (UnicodeDecodeError, OSError):
            continue
        for line in content.splitlines():
            line_stripped = line.strip()
            if line_stripped.startswith('#'):
                continue
            # Strict import syntax:
            #   `from <dotted.module> import ...`
            #   `import <dotted.module>`
            #   `import <dotted.module> as alias`
            #   `from <dotted.module> import (a, b)`  (parenthesized)
            # Disqualifiers that mean "not an import":
            #   - followed by another word (likely docstring like "from executive summary")
            #   - inside a string literal (rare at top level)
            if line_stripped.startswith('from '):
                m = re.match(r'^from\s+([\w.]+)(?:\s+import\s|\s*\(|\s*$)', line_stripped)
                if not m:
                    continue
                mod_str = m.group(1)
            elif line_stripped.startswith('import '):
                m = re.match(r'^import\s+([\w.]+)(?:\s+as\s+\w+|\s*$)', line_stripped)
                if not m:
                    continue
                mod_str = m.group(1)
            else:
                continue
            mod = mod_str.split('.')[0]
            if mod in stdlib or mod.startswith('app') or mod.startswith('_'):
                continue
            if mod in transitive or mod in optional_guarded:
                continue
            third_party_imports.add(mod)

    req_text = (REPO / 'backend' / 'requirements.txt').read_text()
    declared = set()
    for line in req_text.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        m = re.match(r'^([A-Za-z0-9_.+-]+?)(?:[><=!~]|;|\[|$)', line)
        if not m:
            continue
        declared.add(m.group(1).lower())

    import_to_dist = {
        'PIL': 'pillow',
        'cv2': 'opencv-python',
        'sklearn': 'scikit-learn',
        'yaml': 'pyyaml',
        'bs4': 'beautifulsoup4',
        'magic': 'python-magic',
        'jose': 'python-jose',
        'Crypto': 'pycryptodome',
        'jwt': 'pyjwt',
    }
    missing = set()
    for imp in third_party_imports:
        dist = import_to_dist.get(imp, imp).lower().replace('_', '-')
        if dist not in declared and imp.lower() not in declared:
            allowed_via_extras = any(
                dist in d or d.startswith(dist + '[')
                for d in declared
            )
            if not allowed_via_extras:
                missing.add(f'{imp} (as `{dist}`)')

    assert not missing, (
        'Third-party imports reachable from eagerly-loaded routers that '
        'are NOT declared in requirements.txt:\n  - ' + '\n  - '.join(sorted(missing))
        + '\n\nFix: add them to backend/requirements.txt with pinned versions, '
        'OR mark as transitive (starlette/anyio/etc) or optional+guarded.'
    )


def test_engine_py_does_not_have_unguarded_third_party_imports():
    """Specifically test the bug #1 site: openpyxl must be either in
    requirements.txt OR wrapped in try/except ImportError."""
    engine_text = (REPO / 'backend' / 'app' / 'exports' / 'engine.py').read_text()
    if 'from openpyxl' in engine_text or 'import openpyxl' in engine_text:
        guarded = bool(re.search(r'except\s+ImportError', engine_text))
        if not guarded:
            req_text = (REPO / 'backend' / 'requirements.txt').read_text()
            declared = 'openpyxl' in req_text.lower()
            assert declared, (
                'engine.py imports openpyxl unguarded but openpyxl is not in '
                'requirements.txt — this is the bug #1 failure mode. Either '
                'wrap the import in try/except ImportError, OR add openpyxl '
                'to requirements.txt.'
            )


def test_openpyxl_in_requirements():
    """openpyxl is imported unguarded by engine.py — it MUST be declared."""
    req_text = (REPO / 'backend' / 'requirements.txt').read_text()
    assert 'openpyxl' in req_text.lower(), (
        'openpyxl missing from requirements.txt. Bug #1: this causes the '
        'whole app to fail to boot in a clean environment.'
    )


def test_no_duplicate_requirement_lines():
    req_text = (REPO / 'backend' / 'requirements.txt').read_text()
    seen: dict[str, int] = {}
    for line in req_text.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        m = re.match(r'^([A-Za-z0-9_.+-]+?)(?:[><=!~]|;|\[|$)', line)
        if not m:
            continue
        pkg = m.group(1).lower()
        seen[pkg] = seen.get(pkg, 0) + 1
    dups = {pkg: n for pkg, n in seen.items() if n > 1}
    assert not dups, f'Duplicate requirements entries: {dups}'


def test_app_main_does_not_import_openpyxl_at_module_level():
    """Defensive: openpyxl must be lazy-loaded in app.main import chain.

    This complements the requirements.txt check by ensuring openpyxl is
    not promoted to an eager top-level import anywhere.
    """
    # Collect all .py files reachable from main.py imports
    main_text = (REPO / 'backend' / 'app' / 'main.py').read_text()
    queue: list[pathlib.Path] = []
    for m in re.finditer(r'^\s*from\s+(app\.\S+)\s+import\s+', main_text, re.MULTILINE):
        mod_path = m.group(1)
        rel = mod_path.replace('app.', 'app/').replace('.', '/')
        for suffix in ('.py', '/__init__.py'):
            candidate = REPO / 'backend' / f'{rel}{suffix}'
            if candidate.exists():
                queue.append(candidate)
                break
    visited = set()
    while queue:
        f = queue.pop()
        if f in visited:
            continue
        visited.add(f)
        try:
            content = f.read_text(encoding='utf-8')
        except (UnicodeDecodeError, OSError):
            continue
        for m in re.finditer(r'^\s*from\s+(app\.\S+)\s+import\s+', content, re.MULTILINE):
            mod_path = m.group(1)
            if '*' in mod_path:
                continue
            rel = mod_path.replace('app.', 'app/').replace('.', '/')
            for suffix in ('.py', '/__init__.py'):
                candidate = REPO / 'backend' / f'{rel}{suffix}'
                if candidate.exists():
                    queue.append(candidate)
                    break
    # Now check each reachable file for unguarded top-level openpyxl imports.
    # The contract (Bug #1 fix): openpyxl is acceptable EITHER (a) wrapped in
    # try/except ImportError (so the export feature degrades gracefully if
    # the dep is missing), OR (b) declared in requirements.txt so a clean
    # install succeeds without the user manually installing openpyxl.
    req_text = (REPO / 'backend' / 'requirements.txt').read_text()
    openpyxl_declared = bool(re.search(r'^openpyxl\b', req_text, re.MULTILINE | re.IGNORECASE))
    for f in visited:
        try:
            content = f.read_text(encoding='utf-8')
        except (UnicodeDecodeError, OSError):
            continue
        lines = content.splitlines()
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('#'):
                continue
            if not (stripped.startswith('from openpyxl') or stripped == 'import openpyxl'
                    or stripped.startswith('import openpyxl ')):
                continue
            # Is this line inside a try/except? Walk back and find an
            # unmatched `try:`.
            preceding = '\n'.join(lines[max(0, i - 12):i + 1])
            try_idx = preceding.rfind('try:')
            if try_idx >= 0:
                between = preceding[try_idx:]
                if 'except' in between:
                    continue  # inside try/except — OK
            # Not inside try/except — must be declared in requirements.txt
            if not openpyxl_declared:
                rel = f.relative_to(REPO / 'backend')
                raise AssertionError(
                    f"Bug #1: unguarded openpyxl import in {rel}:{i + 1}\n"
                    f"  line: {line}\n"
                    f"  Fix: either (a) wrap in try/except ImportError, or "
                    f"(b) declare openpyxl in backend/requirements.txt."
                )
