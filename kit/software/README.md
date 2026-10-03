# FusionSpace for software projects

## Terminal colour scheme
`terminal/`: Windows Terminal (`windows-terminal.json`, paste into `schemes`), iTerm2 (`FusionSpace.itermcolors`, double-click),
Alacritty (`alacritty.toml`, import it), kitty (`kitty.conf`, `include` it), Ghostty (`ghostty`), VS Code integrated terminal
(`vscode-settings.json`). Background Void, blue O, yellow M orange; red, green and cyan are terminal-only additions picked to sit
with the palette. Preview: `terminal/preview.png`.

## CLI banners
`banner/`: the logo as braille text art in the Fusion gradient: the mark alone (`mark-16`, `mark-24`: 16 and 24 columns wide),
the horizontal lockup (`horizontal-48`, `horizontal-72`, `horizontal-96`: 48, 72 and 96 columns; 72 fits an 80-column terminal)
and the stacked lockup (`stacked-40`), plain (`.txt`) and with 24-bit colour (`.ans`, `cat` it). The name is drawn too, at the
lockup's own proportions, so the banner is the logo, not the mark next to a line of text. The art pads with the empty braille
cell (U+2800), so rows stay aligned even where the font has no braille and the terminal borrows it from another font.
To print it from a program: `cli_banner.py` (`from cli_banner import banner; banner()`: picks the widest banner that fits,
colour on a terminal with a 256-colour fallback, honours `NO_COLOR` and `FORCE_COLOR`), `cli_banner.h` (C/C++) and
`cli_banner.rs` (Rust) with the 72-column banner plain and in colour (`FS_BANNER`, `FS_BANNER_ANSI`), `ascii.txt` (pure ASCII
fallback). Use them for `--version` output, firmware serial-console boot messages, or tool start-up.

## Docs sites
Colours: `color/fusion-space-tokens.css`. Icons: `kit/web/`. Fonts: Cascadia Mono (code, headings), Archivo (body).
