# fusionspace.co: Rev C files

Checked from outside on 2 October 2026. The site still serves the Rev B star cluster in its tab icon (`/icon.svg`), home-screen icon
(`/apple-icon.png`), link preview (`/og.png`) and header logo (`/brand/fusion-space-wordmark.svg`, which also puts the stars after
the wordmark; Rev C allows the mark before it only). Everything here is a drop-in replacement with the same file names.

| Copy | To | Replaces |
|---|---|---|
| `app/icon.svg` | `app/icon.svg` | Rev B stars favicon (Rev C: the cluster on a Void tile) |
| `app/apple-icon.png` | `app/apple-icon.png` | Rev B home-screen icon |
| `app/favicon.ico` | `app/favicon.ico` | nothing (`/favicon.ico` is a 404 today; some tools and old browsers ask for it) |
| `public/icon-192.png`, `public/icon-512.png`, `public/icon-maskable-*.png` | `public/` | the manifest icons (today one file is used as both "any" and "maskable", which crops badly on Android) |
| `public/brand/fusion-space-wordmark.svg` | `public/brand/` | the header logo (Rev C horizontal lockup, gradient) |
| `public/brand/logo-on-white@2x.png` | `public/brand/` | nothing: the email signature's logo, which loads from `https://fusionspace.co/brand/logo-on-white@2x.png` |
| `public/manifest.webmanifest` | `public/manifest.webmanifest` | the manifest (name FusionSpace, Void theme, separate any/maskable icons) |
| `metadata.ts` | merge into `app/layout.tsx` | title, Open Graph, theme colours (name FusionSpace) |
| `public/og.png` | `public/og.png` | the link preview: the stacked lockup with the brand line, Tolerances tight. Ambitions loose. (the same image as `kit/social/og-image-dark.png`) |

The name is **FusionSpace**, one word like the wordmark, in the title, Open Graph, manifest and description. The site's body copy
still says "Fusion Space" in places; change those to one word too.

Colours: the site's theme colour is `#ffffff` / `#09090b` today; the brand's are Paper `#F3F4F7` / Void `#0B0F1C` (set in
`metadata.ts`). The site's buttons use an indigo close to, but not the same as, brand Ion `#3350D6`.
