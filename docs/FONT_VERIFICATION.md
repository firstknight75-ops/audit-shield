# Sorani (ckb) Font Verification

## Required Font

The application uses **Noto Sans Arabic** for both Arabic and Kurdish Sorani
text rendering. This font family includes full coverage for Kurdish
Sorani-specific characters and Persian glyphs.

## Sorani-Specific Glyph Verification

The following Sorani-specific letters must render correctly in the application UI:

| Glyph | Unicode | Name                     |
|-------|---------|--------------------------|
| ھ     | U+06BE  | HEH DOACHASHMEE          |
| ێ     | U+06CE  | KURDISH YEH               |
| ۆ     | U+06C6  | WAW WITH HAMZA ABOVE     |
| ڵ     | U+06B5  | LAM WITH VERTICAL STROKE  |
| ڕ     | U+0695  | REH WITH SMALL V BELOW    |
| ە     | U+06D5  | HEH WITH YEH ABOVE        |

## Test String

For quick manual visual verification, the following sentence uses all six Sorani-specific letters:

**Sorani:** گەورەیی ڕۆڵی ھەژمارەکە پێویستە بۆ ژمێریاری باش، بۆ نموونە ێ و ۆ و ڵ و ڕ و ە.

**Transliteration:** Geuryî rôlî hêjmarêkê pêwîste bo jîmêryarî baş, bo nimûne ê û o û l û r û e.

## Font Source (Self-Hosted — Bug #3 Fix)

Bug #3 (Stabilization pass): previously the docs claimed Noto Sans Arabic was
used but `src/styles.css` actually declared Cairo / Tajawal (neither of which is
bundled), and no font files were present in the repo. On a clean on-premise
deploy with no internet, the UI fell through to the OS default sans-serif which
does NOT guarantee Sorani glyph rendering.

**Now (post-fix):**
- `public/fonts/NotoSansArabic-Regular.woff2` — Regular weight (400), bundled in repo
- `public/fonts/NotoSansArabic-Bold.woff2` — Bold weight (700), bundled in repo
- `src/styles.css` declares matching `@font-face` rules
- The font files were verified at download time to contain all 6 Sorani glyphs
  (see `test_font_assets.py::test_noto_sans_arabic_woff2_contains_all_sorani_glyphs`)
- The font files are loaded directly from `/fonts/...` (relative to the Vite dev
  server / production asset root). **No CDN fetch, no Google Fonts call.**

The PDF export engine uses the **same family** (see
`backend/app/exports/engine.py::PDF_FONT_STACK`), so web UI and exported PDF
share glyph coverage decisions — if a glyph renders in one, it renders in the
other.

Source files (downloaded once, vendored in the repo, no CDN dependency):
- Google Fonts: https://fonts.google.com/noto/specimen/Noto+Sans+Arabic
- SIL Open Font License

## How to Verify

1. Open the application in a browser
2. Switch language to Kurdish Sorani (ckb) via the لغة / زمان toggle
3. Verify all UI labels, error messages, and navigation text renders correctly
4. Specifically check the login page, sidebar navigation, and any error states
5. The browser should NOT issue any network request to fonts.gstatic.com or any
   other font CDN — verify in DevTools → Network → All that the only font requests
   are to `/fonts/NotoSansArabic-*.woff2`
6. Run the build-time check: `pytest backend/.../test_font_assets.py`

## Build-time guard

The test `test_font_assets.py` enforces:
- Both woff2 files exist at `public/fonts/`
- `src/styles.css` declares `@font-face` for "Noto Sans Arabic" with both weights
- The CSS `--font-sans` and `--font-display` reference "Noto Sans Arabic" as
  the primary family
- The woff2 font data contains all 6 required Sorani glyphs (verified via
  fontTools cmap lookup at test time)

If any of these conditions break in a future refactor, the test fails loudly
with a message identifying the drift — preventing a repeat of the
documentation-vs-code gap that produced Bug #3.
