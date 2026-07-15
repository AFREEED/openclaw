#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "opencv-python-headless>=4.9.0",
#     "pillow>=10.0.0",
#     "numpy>=1.26.0",
# ]
# ///
"""
Remove the visible Gemini/Nano Banana "sparkle" badge watermark from an
image, or the Veo watermark badge from a video, by inpainting (images) or
blurring (video) a fixed corner region. This only touches the visible logo
overlay — it does not attempt to defeat SynthID or any other invisible
provenance watermark.

Images:
    uv run remove_watermark.py --input in.png --output out.png

Video (requires ffmpeg on PATH):
    uv run remove_watermark.py --input in.mp4 --output out.mp4

Corner region defaults to the bottom-right, sized as a percentage of the
media's width/height (where Gemini/Veo place the badge). Override with
--corner and --region-pct if the badge sits elsewhere.
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".webm", ".mkv"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}


def compute_box(width: int, height: int, corner: str, region_pct: float) -> tuple[int, int, int, int]:
    """Return (x, y, w, h) of the watermark region for the given corner."""
    w = max(1, int(width * region_pct))
    h = max(1, int(height * region_pct))
    if corner == "bottom-right":
        x, y = width - w, height - h
    elif corner == "bottom-left":
        x, y = 0, height - h
    elif corner == "top-right":
        x, y = width - w, 0
    elif corner == "top-left":
        x, y = 0, 0
    else:
        raise ValueError(f"Unknown corner: {corner}")
    return x, y, w, h


def remove_image_watermark(input_path: Path, output_path: Path, corner: str, region_pct: float) -> None:
    import cv2
    import numpy as np

    img = cv2.imread(str(input_path), cv2.IMREAD_UNCHANGED)
    if img is None:
        print(f"Error: could not read image '{input_path}'", file=sys.stderr)
        sys.exit(1)

    height, width = img.shape[:2]
    x, y, w, h = compute_box(width, height, corner, region_pct)

    mask = np.zeros((height, width), dtype=np.uint8)
    mask[y : y + h, x : x + w] = 255

    # Inpaint only the alpha-free BGR channels; keep alpha untouched if present.
    if img.shape[2] == 4:
        bgr = img[:, :, :3]
        alpha = img[:, :, 3]
        inpainted = cv2.inpaint(bgr, mask, 5, cv2.INPAINT_TELEA)
        result = np.dstack([inpainted, alpha])
    else:
        result = cv2.inpaint(img, mask, 5, cv2.INPAINT_TELEA)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), result)
    print(f"Image saved: {output_path.resolve()}")
    print(f"MEDIA: {output_path.resolve()}")


def remove_video_watermark(input_path: Path, output_path: Path, corner: str, region_pct: float) -> None:
    if shutil.which("ffmpeg") is None:
        print("Error: ffmpeg not found on PATH. Install it to process video.", file=sys.stderr)
        sys.exit(1)

    probe = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height", "-of", "csv=s=x:p=0",
            str(input_path),
        ],
        capture_output=True, text=True,
    )
    if probe.returncode != 0 or not probe.stdout.strip():
        print(f"Error: could not read video dimensions: {probe.stderr}", file=sys.stderr)
        sys.exit(1)

    width_s, height_s = probe.stdout.strip().split("x")
    width, height = int(width_s), int(height_s)
    x, y, w, h = compute_box(width, height, corner, region_pct)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-vf", f"delogo=x={x}:y={y}:w={w}:h={h}:show=0",
        "-c:a", "copy",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running ffmpeg: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    print(f"Video saved: {output_path.resolve()}")
    print(f"MEDIA: {output_path.resolve()}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", "-i", required=True, help="Input image or video path")
    parser.add_argument("--output", "-o", required=True, help="Output path")
    parser.add_argument(
        "--corner", "-c", default="bottom-right",
        choices=["bottom-right", "bottom-left", "top-right", "top-left"],
        help="Corner the watermark badge sits in (default: bottom-right)",
    )
    parser.add_argument(
        "--region-pct", "-p", type=float, default=0.12,
        help="Watermark region size as a fraction of width/height (default: 0.12)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    if not input_path.exists():
        print(f"Error: input file '{input_path}' does not exist", file=sys.stderr)
        sys.exit(1)

    ext = input_path.suffix.lower()
    if ext in VIDEO_EXTS:
        remove_video_watermark(input_path, output_path, args.corner, args.region_pct)
    elif ext in IMAGE_EXTS:
        remove_image_watermark(input_path, output_path, args.corner, args.region_pct)
    else:
        print(f"Error: unsupported file extension '{ext}'", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
