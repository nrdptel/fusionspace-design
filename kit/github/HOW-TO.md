# GitHub setup with the FusionSpace kit

1. **Avatar**: upload `avatar-dark-500.png` (Settings → Profile → Profile picture). Use the same for an organization.
2. **Profile README**: follow `profile-README.md` (a repo named after your username, plus the two banner PNGs).
3. **Each repository**:
   - Social preview: Settings → General → Social preview → upload `social-preview-dark.png`, or a per-project one made with
     `python3 tools/build/project.py --name <Star> --tag <TAG> --desc "..."` (example in `kit/projects/example-vega/`).
   - README header: copy the project's `readme-banner-dark.png` and `-light.png` into `.github/brand/` and start from its
     `README-starter.md` (or use the brand banners here with `README-snippet.md`).
   - Labels: `./apply-labels.sh owner/repo` (needs the GitHub CLI, `gh`). Colors come from the palette; see `labels.json`.
   - Badges: `badges.md`.
   - Topics: add `fusionspace` plus the discipline (e.g. `embedded`, `pcb`, `cnc`, `game`) so projects are easy to filter.
4. **GitHub Pages or a docs site**: use `kit/web/` for the icon set and `kit/software/docs-theme/` (MkDocs Material or Docusaurus) for the look; `color/fusion-space-tokens.css` has the raw colors.
