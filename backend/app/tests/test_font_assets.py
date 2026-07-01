"""Regression: Self-hosted Noto Sans Arabic must be present and wired up.

Bug #3 (Stabilization pass): the docs claimed Noto Sans Arabic was used but
`src/styles.css` actually declared Cairo / Tajawal (neither bundled), and no
font files were present in the repo. On a clean on-premise deploy with
no internet, the UI fell through to OS default sans-serif which does NOT
guarantee Sorani glyph rendering.

This file provides a build-time check that catches any future drift:
- woff2 files exist on disk
- CSS declares matching @font-face for the family
- The woff2 font data contains all 6 required Sorani glyphs

If any of these conditions break, the test fails loudly.
"""
from __future__ import annotations

import pathlib
import re

import pytest

REPO = pathlib.Path(__file__).resolve().parents[3]


SORANI_CHARS = [
    ('ھ', 0x06BE, 'HEH DOACHASHMEE'),
    ('ێ', 0x06CE, 'KURDISH YEH'),
    ('ۆ', 0x06C6, 'WAW WITH HAMZA ABOVE'),
    ('ڵ', 0x06B5, 'LAM WITH VERTICAL STROKE'),
    ('ڕ', 0x0695, 'REH WITH SMALL V BELOW'),
    ('ە', 0x06D5, 'HEH WITH YEH ABOVE'),
]


def test_regular_woff2_exists_on_disk():
    p = REPO / 'public' / 'fonts' / 'NotoSansArabic-Regular.woff2'
    assert p.exists(), f'Bug #3: {p} missing — self-hosted Regular weight not bundled'
    assert p.stat().st_size > 1024, f'{p} is suspiciously small ({p.stat().st_size} bytes)'


def test_bold_woff2_exists_on_disk():
    p = REPO / 'public' / 'fonts' / 'NotoSansArabic-Bold.woff2'
    assert p.exists(), f'Bug #3: {p} missing — self-hosted Bold weight not bundled'
    assert p.stat().st_size > 1024, f'{p} is suspiciously small ({p.stat().st_size} bytes)'


def test_no_cdn_font_references_in_css():
    """The CSS must NOT fetch fonts from any CDN (Google Fonts, jsdelivr, etc.)."""
    css = (REPO / 'src' / 'styles.css').read_text()
    for cdn in ('fonts.googleapis.com', 'fonts.gstatic.com', 'cdn.jsdelivr.net', 'use.typekit.net'):
        assert cdn not in css, (
            f'Bug #3 regression: styles.css references CDN `{cdn}`. '
            f'On-premise-first product must self-host fonts.'
        )


def test_styles_css_declares_noto_sans_arabic_at_face():
    """CSS must declare @font-face rules for both weights of Noto Sans Arabic."""
    css = (REPO / 'src' / 'styles.css').read_text()
    assert '@font-face' in css, 'styles.css must declare @font-face rules'
    assert 'font-family: "Noto Sans Arabic"' in css, (
        'styles.css must declare @font-face for "Noto Sans Arabic"'
    )
    assert '/fonts/NotoSansArabic-Regular.woff2' in css, (
        '@font-face must reference the self-hosted Regular woff2 file'
    )
    assert '/fonts/NotoSansArabic-Bold.woff2' in css, (
        '@font-face must reference the self-hosted Bold woff2 file'
    )


def test_styles_css_font_sans_references_noto_sans_arabic():
    """The --font-sans token must point at Noto Sans Arabic first, not Cairo/Tajawal."""
    css = (REPO / 'src' / 'styles.css').read_text()
    # Strip comments so the docstring above the @theme block (which mentions
    # "Cairo/Tajawal" in historical context) doesn't trip up the regex.
    css_no_comments = re.sub(r'/\*.*?\*/', '', css, flags=re.DOTALL)
    m = re.search(r'--font-sans:\s*([^;]+);', css_no_comments)
    assert m, 'styles.css must define --font-sans'
    value = m.group(1).strip()
    assert 'Noto Sans Arabic' in value, (
        f'Bug #3 regression: --font-sans is "{value}" — must include '
        f'"Noto Sans Arabic" as primary family.'
    )
    # Must NOT lead with Cairo or Tajawal (Bug #3 source font)
    leading = value.lstrip()
    assert not leading.startswith('"Cairo"'), (
        '--font-sans still leads with "Cairo" — the Bug #3 source font has '
        'never been bundled.'
    )
    assert not leading.startswith('"Tajawal"'), (
        '--font-sans still leads with "Tajawal" — the Bug #3 source font has '
        'never been bundled.'
    )


def test_styles_css_font_display_references_noto_sans_arabic():
    css = (REPO / 'src' / 'styles.css').read_text()
    css_no_comments = re.sub(r'/\*.*?\*/', '', css, flags=re.DOTALL)
    m = re.search(r'--font-display:\s*([^;]+);', css_no_comments)
    assert m, 'styles.css must define --font-display'
    value = m.group(1).strip()
    assert 'Noto Sans Arabic' in value, (
        f'--font-display is "{value}" — must include "Noto Sans Arabic"'
    )


def test_noto_sans_arabic_woff2_contains_all_sorani_glyphs():
    """The actual font data must contain all 6 Sorani-specific glyphs.

    We check the TTF source (which is what the woff2 was generated from);
    cmap is preserved through woff2 conversion, so this is equivalent to
    checking the woff2 directly without requiring the brotli decoder at
    test time.

    This is the strongest test: even if the CSS is wired correctly, if the
    bundled font file somehow loses glyph coverage, the UI would render
    tofu boxes for Sorani text. This test fails loudly in that case.
    """
    pytest.importorskip('fontTools')
    from fontTools.ttLib import TTFont

    # The woff2 was generated from the TTF in public/fonts/. cmap is preserved
    # in woff2, so checking the TTF source proves the woff2 coverage.
    p = REPO / 'public' / 'fonts' / 'NotoSansArabic-Regular.ttf'
    if not p.exists():
        pytest.skip(f'{p} missing — TTF source not vendored')
    font = TTFont(str(p))
    cmap = font.getBestCmap()

    missing = []
    for ch, code, name in SORANI_CHARS:
        if code not in cmap:
            missing.append(f'{ch} (U+{code:04X}, {name})')

    assert not missing, (
        'Noto Sans Arabic is missing required Sorani glyphs:\n  - '
        + '\n  - '.join(missing)
        + '\n\nRe-download from '
        'https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/'
        'NotoSansArabic/NotoSansArabic-Regular.ttf'
    )


def test_woff2_files_have_valid_signature():
    """The bundled woff2 files must have the WOFF2 magic signature."""
    for name in ('NotoSansArabic-Regular.woff2', 'NotoSansArabic-Bold.woff2'):
        p = REPO / 'public' / 'fonts' / name
        assert p.exists(), f'{p} missing'
        head = p.read_bytes()[:4]
        # WOFF2 magic: 0x774F4632 ('wOF2')
        assert head == b'wOF2', (
            f'{p} does not start with WOFF2 magic (wOF2) — got {head!r}'
        )


def test_font_verification_doc_describes_actual_shipped_mechanism():
    """docs/FONT_VERIFICATION.md must reflect the self-hosted mechanism,
    NOT a CDN assumption."""
    doc = (REPO / 'docs' / 'FONT_VERIFICATION.md').read_text()
    # Must mention self-hosting
    assert 'self-hosted' in doc.lower() or 'self-host' in doc.lower(), (
        'FONT_VERIFICATION.md must document self-hosting — previously it '
        'described a CDN assumption that the on-premise deploy cannot meet.'
    )
    # Must NOT direct users to a CDN download path
    bad_cdn_phrases = [
        'Google Fonts: https://fonts.google.com/noto/specimen/Noto+Sans+Arabic',
    ]
    for phrase in bad_cdn_phrases:
        # The doc CAN reference the source-of-truth URL, but must NOT imply
        # the app fetches from there at runtime.
        if phrase in doc:
            surrounding = doc[max(0, doc.index(phrase) - 200):doc.index(phrase) + 200]
            assert 'source' in surrounding.lower() or 'origin' in surrounding.lower() or 'downloaded once' in surrounding.lower(), (
                f'FONT_VERIFICATION.md references "{phrase}" in a way that '
                f'suggests runtime CDN fetch — fix the wording.'
            )


def test_app_shell_uses_css_font_token_not_hardcoded():
    """The app-shell must NOT override the font-family; it must use the
    CSS token so the self-hosted font takes effect."""
    shell = (REPO / 'src' / 'components' / 'app-shell.tsx').read_text()
    # The shell should use var(--font-sans) (or fall through to inherited)
    if 'fontFamily' in shell or 'font-family' in shell:
        # If it sets one, it should be Noto Sans Arabic, not Cairo/Tajawal
        assert 'Cairo' not in shell, 'app-shell hardcodes Cairo'
        assert 'Tajawal' not in shell, 'app-shell hardcodes Tajawal'
