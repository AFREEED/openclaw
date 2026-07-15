---
name: gemini-watermark-remover
description: Remove the visible Gemini/Nano Banana "sparkle" badge from images, or the Veo badge from videos, by inpainting/blurring the corner logo.
homepage: https://ai.google.dev/
metadata:
  {
    "openclaw":
      {
        "emoji": "🩹",
        "requires": { "bins": ["uv"] },
        "install":
          [
            {
              "id": "uv-brew",
              "kind": "brew",
              "formula": "uv",
              "bins": ["uv"],
              "label": "Install uv (brew)",
            },
          ],
      },
  }
---

# Gemini Watermark Remover

Removes the small visible watermark badge (the sparkle logo Gemini/Nano
Banana stamps on generated images, or the badge Veo stamps on generated
videos) from a corner of the media. Images are fixed via inpainting
(content-aware fill); video uses ffmpeg's `delogo` filter over the same
corner region, frame by frame.

This only touches the visible logo overlay. It does not attempt to
detect or strip SynthID or any other invisible provenance watermark —
that is a deliberate scope limit, not a missing feature.

## Run

Image:

```bash
uv run {baseDir}/scripts/remove_watermark.py --input in.png --output out.png
```

Video (requires `ffmpeg` on PATH):

```bash
uv run {baseDir}/scripts/remove_watermark.py --input in.mp4 --output out.mp4
```

Flags:

- `--corner` — which corner the badge sits in: `bottom-right` (default),
  `bottom-left`, `top-right`, `top-left`.
- `--region-pct` — size of the watermark region as a fraction of
  width/height (default `0.12`). Increase if the badge isn't fully
  covered; decrease if too much of the image/video gets touched.

## Notes

- Requires `uv` (bundles its own Python deps: `opencv-python-headless`,
  `pillow`, `numpy`) and, for video, a system `ffmpeg`/`ffprobe`.
- The script prints a `MEDIA:` line for OpenClaw to auto-attach on
  supported chat providers.
- If the default corner/region doesn't fully cover the badge, re-run
  with adjusted `--corner`/`--region-pct` rather than tweaking the script.
