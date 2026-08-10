<!--
File: README.md
Path: assets/README.md
Role: Index for marketplace logo, README hero video, and tutorial screenshots.
Used By:
 - README.md (logo + hero video + install walkthrough)
 - .cursor-plugin/plugin.json (logo)
 - .ai_infra/docs/operations/consumer-quickstart.md
Depends On:
 - assets/agent-colony-logo.png
 - assets/img/tutorials_img/*.png
Notes:
 - GitHub README video requires a user-attachments or release CDN URL — not a relative path.
 - Tutorial PNGs are ~1920×1080; docs display at width 800 with click-to-open full size.
-->

# Plugin assets

Marketplace logotype, README hero media, and onboarding screenshots for **Agent Colony** (`agent-colony`).

## Layout

```text
assets/
├── agent-colony-logo.png          # Marketplace + README brand mark
├── img/
│   ├── tutorials_img/             # Onboarding walkthrough (01–17)
│   │   └── NN_tutorial_agent-colony.png
│   ├── agent-colony-img/          # Brand still variants
│   └── agent_colony_img/          # Brand still variants (alt folder)
└── video/
    └── agent-colony-hero.mp4      # Source MP4 (README uses user-attachments CDN URL)
```

## Screenshot standard (docs)

All tutorial images use the same HTML block so users can open full resolution and zoom in the browser:

```html
<p align="center">
  <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/NN_tutorial_agent-colony.png" title="Open full resolution (1920×1080)">
    <img src="assets/img/tutorials_img/NN_tutorial_agent-colony.png" alt="…" width="800" />
  </a>
</p>
<p align="center"><sub>Step N — caption · <a href="…raw…">Full size</a> · browser zoom <kbd>Ctrl</kbd>+<kbd>+</kbd> / <kbd>−</kbd></sub></p>
```

From **consumer-shipped** docs (`.ai_infra/docs/operations/*.md`), use the **raw GitHub URL** for both `href` and `src` so images work in activated app repos (they do not copy `assets/`). Kit **README** may use relative `assets/img/tutorials_img/` paths.

## Tutorial screenshots

| File | Step | Shows |
|------|------|--------|
| `01_tutorial_agent-colony.png` | 1a | Agent chat: `/add-plugin` URL + Agent Colony preview card |
| `02_tutorial_agent-colony.png` | 1b | Select app project → **Add Plugin** |
| `03_tutorial_agent-colony.png` | 1c | Plugin installing |
| `04_tutorial_agent-colony.png` | 2 | `/workflow-activate` in Agent chat (pick from menu) |
| `05_tutorial_agent-colony.png` | 3 | After activate — edit `github.collaboration.yaml` (`display_name`, `github_user`) |
| `06_tutorial_agent-colony.png` | 3 | `contributors validate` → PASS |
| `07_tutorial_agent-colony.png` | 3b | New GitHub Project + default repository |
| `08_tutorial_agent-colony.png` | 3c | `/board` — Project + repo URLs; YAML Board Identity updated |
| `09_tutorial_agent-colony.png` | 4a | First Project view — board agent turn instructions |
| `10_tutorial_agent-colony.png` | 4b | Prioritized backlog + Status board; agent configuring columns |
| `11_tutorial_agent-colony.png` | 4c | Board agent in IDE browser — view setup (continued) |
| `12_tutorial_agent-colony.png` | 4d | Prioritized backlog columns |
| `13_tutorial_agent-colony.png` | Ref | Reference board — Prioritized backlog (kit repo example) |
| `14_tutorial_agent-colony.png` | Ref | Reference board — Status board columns |
| `15_tutorial_agent-colony.png` | Ref | Draft cards (P0–P2) via board agent in chat |
| `16_tutorial_agent-colony.png` | MCP | DeepWiki MCP in Agent chat (`karpathy/nanochat`) |
| `17_tutorial_agent-colony.png` | MCP | DeepWiki CLI `mcp call` success |

**Wired in:** [README § Install](../README.md#install-consumers) (key steps) · [consumer-quickstart](../.ai_infra/docs/operations/consumer-quickstart.md#visual-walkthrough) (full gallery)

## Files

| File | Use |
|------|-----|
| `agent-colony-logo.png` | Marketplace logotype + README brand mark (`<img>`, ~180px wide) |
| `img/tutorials_img/01_…` | Replaces legacy `agent-colony-install.png` for `/add-plugin` preview |
| `video/agent-colony-hero.mp4` | Source for the short “at work” hero clip |
| `img/agent-colony-img/*`, `img/agent_colony_img/*` | Brand variants / marketing stills (not wired into README by default) |

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

Publisher: Savin Ionuț Răzvan · [razvansavin.com](https://razvansavin.com/) · [GitHub](https://github.com/SavinRazvan)
