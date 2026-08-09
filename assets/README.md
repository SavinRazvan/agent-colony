# Plugin assets

Marketplace logotype, README hero media, and docs screenshots for **Agent Colony** (`agent-colony`).

## Layout

```text
assets/
├── agent-colony-logo.png          # Marketplace + README poster / fallback
├── agent-colony-install.png       # README install screenshot
├── img/                           # Extra brand stills (variants)
│   ├── agent-colony-logo.png
│   ├── agent-colony-logo-01.png … 06.png
│   └── agent-colony-4-cursor.png
└── video/
    └── agent-colony-hero.mp4      # README hero loop (also on release tag `media`)
```

## Files

| File | Use |
|------|-----|
| `agent-colony-logo.png` | Marketplace logotype + README `<video poster>` / fallback `<img>` |
| `agent-colony-install.png` | Root `README.md` § Install — `/add-plugin` preview |
| `video/agent-colony-hero.mp4` | README hero loop (committed + mirrored on release `media`) |
| `img/*` | Brand variants / marketing stills (not wired into README by default) |

**Consumer copy:** install screenshot also ships at `.ai_infra/docs/operations/assets/agent-colony-install.png`.

## README hero video

GitHub README only plays `<video>` when `src` is a **GitHub CDN URL** (release download or `user-attachments`). Relative paths like `assets/video/….mp4` are stripped.

Current README uses the **`media`** release asset (GitHub CDN — required for `<video>`):

```text
https://github.com/SavinRazvan/agent-colony/releases/download/media/agent-colony-hero.mp4
```

(`gh release download media -p agent-colony-hero.mp4` works; browsers use the same URL.)

Replace the release asset after re-encoding:

```bash
gh release upload media assets/video/agent-colony-hero.mp4 --clobber
```

Attributes: `autoplay` `loop` `muted` `playsinline` (required for silent autoplay). Keep `poster` + nested `<img>` so non-video clients still see the logo.

## Marketplace logotype

**`agent-colony-logo.png`** (1:1 PNG). After commit to `main`:

```text
https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/agent-colony-logo.png
```

Plugin field: `.cursor-plugin/plugin.json` → `"logo": "assets/agent-colony-logo.png"` (must stay an image, not video).

## Install screenshot

`agent-colony-install.png` — Agent chat with `/add-plugin` and the **Agent Colony** preview card.

Publisher: Savin Ionuț Răzvan · [razvansavin.com](https://razvansavin.com/) · [GitHub](https://github.com/SavinRazvan)
