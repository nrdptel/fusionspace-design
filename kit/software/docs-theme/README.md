# FusionSpace docs-site themes

- **MkDocs Material**: copy `mkdocs/fusionspace.css` to `docs/stylesheets/`, `type/fonts/*.ttf` to `docs/fonts/`, and merge
  `mkdocs/mkdocs.yml` into your config (light/dark palettes follow the reader's system setting).
- **Docusaurus**: use `docusaurus/custom.css` as `src/css/custom.css`; put the fonts in `static/fonts/` and change `../fonts/`
  to `/fonts/`. Set the navbar logo to `kit/web/favicon.svg`.

Both apply the brand tokens: Paper/Void pages, white/Abyss surfaces, Ion (light) and O blue (dark) links, Archivo body text,
Cascadia Mono headings and code, and the Fusion gradient as a 3 px line under the header. `docs-preview-*.png` show the look.
