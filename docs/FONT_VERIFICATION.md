# Sorani (ckb) Font Verification

## Required Font

The application uses **Noto Sans Arabic** (and optionally Noto Sans Arabic UI) for both Arabic and Kurdish Sorani text rendering. This font family includes full coverage for Kurdish Sorani-specific characters.

## Sorani-Specific Glyph Verification

The following Sorani-specific letters must render correctly in the application UI:

| Glyph | Unicode | Name                     | Rendered |
|-------|---------|--------------------------|----------|
| ھ     | U+06BE  | HEH DOACHASHMEE         | ھ        |
| ێ     | U+06CE  | KURDISH YEH              | ێ        |
| ۆ     | U+06C6  | WAW WITH HAMZA ABOVE     | ۆ        |
| ڵ     | U+06B5  | LAM WITH VERTICAL STROKE | ڵ        |
| ڕ     | U+0695  | REH WITH SMALL V BELOW   | ڕ        |
| ە     | U+06D5  | HEH WITH YEH ABOVE       | ە        |

## Test String

For quick manual visual verification, the following sentence uses all six Sorani-specific letters:

**Sorani:** گەورەیی ڕۆڵی ھەژمارەکە پێویستە بۆ ژمێریاری باش، بۆ نموونە ێ و ۆ و ڵ و ڕ و ە.

**Transliteration:** Geuryî rôlî hêjmarêkê pêwîste bo jîmêryarî baş, bo nimûne ê û o û l û r û e.

## Font Source

- Google Fonts: https://fonts.google.com/noto/specimen/Noto+Sans+Arabic
- Includes full Arabic, Kurdish Sorani, and Persian glyph support
- SIL Open Font License

## How to Verify

1. Open the application in a browser
2. Switch language to Kurdish Sorani (ckb) via the لغة / زمان toggle
3. Verify all UI labels, error messages, and navigation text renders without square boxes or fallback characters
4. Specifically check the login page, sidebar navigation, and any error states
5. The CSS `font-family` is set to `'Noto Sans Arabic', 'Noto Sans Arabic UI', sans-serif`
6. If the font is not loaded (e.g., in the sandboxed preview), downloaded files will render correctly in a full browser with the font installed or loaded from Google Fonts CDN

## Notes

- The application uses `dir="rtl"` on the root shell for both `ar` and `ckb` locales
- CSS logical properties should be used instead of `left`/`right` where possible
- The `Noto Sans Arabic` font weight 400 (Regular) and 700 (Bold) are the minimum required weights
