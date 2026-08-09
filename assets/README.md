<!--
File: README.md
Path: assets/README.md
Role: Index for marketplace logo, README hero video, and install screenshot.
Used By:
 - README.md (logo + hero video + install screenshot)
 - .cursor-plugin/plugin.json (logo)
Depends On:
 - assets/agent-colony-logo.png
 - assets/agent-colony-install.png
Notes:
 - GitHub README video requires a user-attachments or release CDN URL — not a relative path.
-->

# Plugin assets

Marketplace logotype, README hero media, and docs screenshots for **Agent Colony** (`agent-colony`).

## Layout

```text
assets/
├── agent-colony-logo.png          # Marketplace + README brand mark (top of README)
├── agent-colony-install.png       # README install screenshot
├── img/                           # Extra brand stills (variants)
│   ├── agent-colony-logo.png
│   ├── agent-colony-logo-01.png … 06.png
│   └── agent-colony-4-cursor.png
└── video/
    └── agent-colony-hero.mp4      # Source MP4 (README uses user-attachments CDN URL)
```

## Files

| File | Use |
|------|-----|
| `agent-colony-logo.png` | Marketplace logotype + README brand mark (`<img>`, ~180px wide) |
| `agent-colony-install.png` | Root `README.md` § Install — `/add-plugin` preview |
| `video/agent-colony-hero.mp4` | Source for the short “at work” hero clip |
| `img/*` | Brand variants / marketing stills (not wired into README by default) |

**Consumer copy:** install screenshot also ships at `.ai_infra/docs/operations/assets/agent-colony-install.png`.

## README hero order

1. **Logo** — relative path `assets/agent-colony-logo.png` (images work from the repo).
2. **Title + pitch** — `# Agent Colony` and the one-line tagline.
3. **Video** — short mascot / “at work” clip via GitHub CDN (see below).

## README hero video

GitHub README only plays `<video>` when `src` is a **GitHub CDN URL** (`user-attachments` or release download). Relative paths like `assets/video/….mp4` are stripped.

Current README uses a **user-attachments** URL (upload the MP4 into an issue/PR comment, copy the generated link):

```text
https://github.com/user-attachments/assets/f9015ab5-28bf-47f7-a065-2127c098b80e
```

Optional mirror on release tag `media` (downloadable, not required for README play):

```bash
gh release upload media assets/video/agent-colony-hero.mp4 --clobber
```

Prefer a modest width (e.g. `width="720"`). GitHub’s player shows the first frame; click to play — do not rely on `autoplay` / `loop` / `poster`.

## Marketplace logotype

**`agent-colony-logo.png`** (1:1 PNG, currently 627×627). After commit to `main`:

```text
https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/agent-colony-logo.png
```

Plugin field: `.cursor-plugin/plugin.json` → `"logo": "assets/agent-colony-logo.png"` (must stay an image, not video).

## Install screenshot

`agent-colony-install.png` — Agent chat with `/add-plugin` and the **Agent Colony** preview card.

Publisher: Savin Ionuț Răzvan · [razvansavin.com](https://razvansavin.com/) · [GitHub](https://github.com/SavinRazvan)
