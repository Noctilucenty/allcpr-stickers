#!/usr/bin/env python3
"""
Build the ALLCPR WeChat sticker pack (表情包) from the generated animations.

Pipeline per sticker:
  mp4 (960x960, 24fps, 3s)
    -> extract frames with ffmpeg
    -> flood-fill the background to pure white from the borders
    -> find the union bounding box of "strong art" (dark-outlined pixels) across
       the whole clip, and force everything outside it to white. This removes the
       light-grey rectangle the image model drew when asked for an "empty band",
       without touching any real artwork.
    -> crop to that box, scale into the art zone, bottom-anchored above a
       reserved caption band so the caption never covers the character
    -> typeset the Chinese caption with Pillow (never model-drawn, always correct)
    -> downscale to 240x240
    -> encode GIF with one global palette and no dithering
    -> gifsicle ladder until the file fits WeChat's 100KB ceiling

WeChat 表情开放平台 spec: main sticker 240x240 GIF <=100KB, thumbnail 240x240 PNG
<=60KB, 16 or 24 stickers per set.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent
VIDEO = ROOT / "03_video"
FRAMES = ROOT / "04_frames"
GIFS = ROOT / "05_gif"

WORK = 480            # working resolution, downscaled to FINAL at the end
FINAL = 240           # WeChat main sticker size
SIZE_LIMIT = 100_000  # WeChat main sticker byte ceiling
BASE_FPS = 24         # source fps

FONT_PATH = "/System/Library/Fonts/Hiragino Sans GB.ttc"
FONT_INDEX = 2        # W6 (bold)

FLOOD_THRESH = 90     # background flood-fill tolerance from pure white
ART_DARK = 150        # a pixel is "strong art" when its darkest channel is below this

ART_TOP = int(WORK * 0.015)     # art zone
ART_BOTTOM = int(WORK * 0.815)  # caption band starts here
CAP_H = WORK - ART_BOTTOM
SIDE_PAD = int(WORK * 0.035)

# (stride from 24fps, colours, gifsicle lossy level) - colour fidelity first,
# frame count second, lossy last.
LADDER = [
    (2, 200, 0), (2, 160, 0), (3, 160, 0), (3, 128, 30), (4, 128, 30),
    (4, 96, 60), (5, 96, 60), (5, 80, 90), (6, 80, 90), (6, 64, 120),
    (8, 64, 120), (8, 48, 150), (8, 32, 180),
]


def run(cmd):
    subprocess.run(cmd, check=True, capture_output=True)


def extract_frames(sid):
    out = FRAMES / sid
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    run([
        "ffmpeg", "-v", "error", "-i", str(VIDEO / f"{sid}.mp4"),
        "-vf", f"scale={WORK}:{WORK}:flags=lanczos",
        str(out / "f_%03d.png"),
    ])
    return sorted(out.glob("f_*.png"))


def clean_background(im):
    """Flood the background to pure white from every border seed, then wipe the
    pale neutral greys left behind by the model's "empty band" rectangle.
    The neutral test (near-zero saturation) and the high floor both keep this
    away from real linework, which is either darker or clearly tinted."""
    w, h = im.size
    seeds = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1),
             (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2)]
    for xy in seeds:
        ImageDraw.floodfill(im, xy, (255, 255, 255), thresh=FLOOD_THRESH)

    px = im.load()
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            lo, hi = min(r, g, b), max(r, g, b)
            if lo >= 185 and (hi - lo) <= 12:
                px[x, y] = (255, 255, 255)
    return im


def art_bbox(im):
    """Box around pixels dark enough to be real linework. Deliberately ignores
    the pale grey rectangle artifact, which never goes below ART_DARK."""
    px = im.load()
    w, h = im.size
    minx, miny, maxx, maxy = w, h, -1, -1
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            if r < ART_DARK or g < ART_DARK or b < ART_DARK:
                if x < minx: minx = x
                if x > maxx: maxx = x
                if y < miny: miny = y
                if y > maxy: maxy = y
    if maxx < 0:
        return None
    return minx, miny, maxx, maxy


def union(a, b):
    if a is None:
        return b
    if b is None:
        return a
    return min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])


def fit_font(text, max_w, max_h):
    size = max_h
    while size > 8:
        f = ImageFont.truetype(FONT_PATH, size, index=FONT_INDEX)
        box = f.getbbox(text)
        if (box[2] - box[0]) <= max_w and (box[3] - box[1]) <= max_h:
            return f
        size -= 2
    return ImageFont.truetype(FONT_PATH, 10, index=FONT_INDEX)


def draw_caption(canvas, text):
    """Black glyphs, white halo, black outer keyline - the standard 表情包
    caption treatment, readable against any chat background."""
    d = ImageDraw.Draw(canvas)
    font = fit_font(text, WORK - 2 * SIDE_PAD, int(CAP_H * 0.86))

    box = font.getbbox(text)
    tw, th = box[2] - box[0], box[3] - box[1]
    x = (WORK - tw) // 2 - box[0]
    y = ART_BOTTOM + (CAP_H - th) // 2 - box[1]

    size = font.size
    w_outer = max(3, round(size * 0.135))
    w_mid = max(2, round(size * 0.085))

    d.text((x, y), text, font=font, fill="black", stroke_width=w_outer, stroke_fill="black")
    d.text((x, y), text, font=font, fill="white", stroke_width=w_mid, stroke_fill="white")
    d.text((x, y), text, font=font, fill="black")
    return canvas


def build_frames(sid, caption):
    paths = extract_frames(sid)
    cleaned, box = [], None
    for p in paths:
        im = clean_background(Image.open(p).convert("RGB"))
        cleaned.append(im)
        box = union(box, art_bbox(im))

    pad = 4
    x0 = max(0, box[0] - pad); y0 = max(0, box[1] - pad)
    x1 = min(WORK, box[2] + pad); y1 = min(WORK, box[3] + pad)
    bw, bh = x1 - x0, y1 - y0

    zone_w, zone_h = WORK - 2 * SIDE_PAD, ART_BOTTOM - ART_TOP
    scale = min(zone_w / bw, zone_h / bh)
    nw, nh = max(1, round(bw * scale)), max(1, round(bh * scale))
    ox = (WORK - nw) // 2
    oy = ART_BOTTOM - nh          # bottom-anchored, sitting on the caption band

    out = []
    for im in cleaned:
        canvas = Image.new("RGB", (WORK, WORK), "white")
        canvas.paste(im.crop((x0, y0, x1, y1)).resize((nw, nh), Image.LANCZOS), (ox, oy))
        draw_caption(canvas, caption)
        out.append(canvas.resize((FINAL, FINAL), Image.LANCZOS))
    return out


def encode(frames, stride, colors, lossy, dest):
    """One global palette, no dithering - flat cel art compresses hard this way."""
    sel = frames[::stride]
    if len(sel) < 4:
        sel = frames[:4]

    strip = Image.new("RGB", (FINAL, FINAL * len(sel)))
    for i, f in enumerate(sel):
        strip.paste(f, (0, FINAL * i))
    pal = strip.quantize(colors=colors, method=Image.Quantize.MEDIANCUT)

    q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in sel]
    duration = round(1000 * stride / BASE_FPS)

    q[0].save(dest, save_all=True, append_images=q[1:],
              duration=duration, loop=0, optimize=True, disposal=2)

    cmd = ["gifsicle", "-O3", "--no-warnings", f"--colors={colors}"]
    if lossy:
        cmd.append(f"--lossy={lossy}")
    cmd += ["-o", str(dest), str(dest)]
    run(cmd)
    return dest.stat().st_size, len(sel)


def main():
    spec = json.loads((ROOT / "captions.json").read_text())
    GIFS.mkdir(exist_ok=True)
    FRAMES.mkdir(exist_ok=True)

    only = sys.argv[1:] or None
    report = []

    for s in spec["stickers"]:
        sid, caption = s["id"], s["caption"]
        if only and sid not in only:
            continue
        if not (VIDEO / f"{sid}.mp4").exists():
            print(f"{sid}  MISSING mp4")
            continue

        frames = build_frames(sid, caption)
        dest = GIFS / f"{sid}.gif"

        for stride, colors, lossy in LADDER:
            size, n = encode(frames, stride, colors, lossy, dest)
            if size <= SIZE_LIMIT:
                break

        # thumbnail: first frame as PNG, <=60KB
        thumb = GIFS / f"{sid}_thumb.png"
        frames[0].save(thumb, optimize=True)

        status = "ok " if size <= SIZE_LIMIT else "OVER"
        print(f"{sid} {caption:<6} {status} {size/1000:6.1f}KB  {n:2d}f  "
              f"{colors:3d}c  lossy={lossy}  thumb {thumb.stat().st_size/1000:.1f}KB")
        report.append({
            "id": sid, "caption": caption, "bytes": size, "frames": n,
            "colors": colors, "lossy": lossy, "within_limit": size <= SIZE_LIMIT,
            "thumb_bytes": thumb.stat().st_size,
        })

    (ROOT / "build_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
    over = [r for r in report if not r["within_limit"]]
    fat = [r for r in report if r["thumb_bytes"] > 60_000]
    print(f"\n{len(report)} stickers, {len(over)} over {SIZE_LIMIT/1000:.0f}KB, "
          f"{len(fat)} thumbnails over 60KB")


if __name__ == "__main__":
    main()
