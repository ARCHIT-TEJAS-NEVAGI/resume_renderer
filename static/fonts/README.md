# Self-hosted fonts (optional)

By default the templates use a modern system font stack (no network requests,
fully ATS-friendly and print-safe). If you want a custom typeface, drop the
font files into this directory and restart the service — the template manager
inlines them as base64 data URIs into every generated document, so they work
in the HTML response **and** in the Playwright-generated PDF.

## Filename convention

Use `FamilyName-Weight.ext`:

```
Inter-Regular.woff2
Inter-Medium.woff2
Inter-SemiBold.woff2
Inter-Bold.woff2
Inter-Black.woff2
Inter-Italic.woff2
Inter-BoldItalic.woff2
```

Supported extensions: `.woff2`, `.woff`, `.ttf`, `.otf`.

Recognized weight tokens: `Thin`, `Extralight`, `Light`, `Regular`, `Medium`,
`SemiBold`, `Bold`, `ExtraBold`, `Black`, plus `Italic` and combinations such
as `BoldItalic`.

All files for a family must share the same `FamilyName` (e.g. `Inter`), and
all variants of one family should be in this single directory. Files that do
not match the convention are skipped with a warning at startup.

## Notes

- Keep the total font size reasonable — fonts are embedded in every response.
- The first discovered family becomes the default; the base CSS defines
  `--font-sans` and `--font-serif`, so a serif family added here is used by
  the serif-based templates (classic, executive) automatically.
