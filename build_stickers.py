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
import os
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).parent
VIDEO = ROOT / "03_video"
FRAMES = ROOT / "04_frames"

WORK = 480            # working resolution, downscaled to FINAL at the end
FINAL = 240           # WeChat main sticker size
SIZE_LIMIT = 100_000  # WeChat main sticker byte ceiling
BASE_FPS = 12         # frames are extracted at this rate

# Per-language caption face. The Chinese set uses Hiragino Sans GB W6; the English
# set uses Arial Black, which carries the same heavy 表情包 weight in Latin.
FONTS = {
    "zh": ("/System/Library/Fonts/Hiragino Sans GB.ttc", 2, 0.84),
    "en": ("/System/Library/Fonts/Supplemental/Arial Black.ttf", 0, 0.92),
}
LANG = os.environ.get("LANG_SET", "zh")
FONT_PATH, FONT_INDEX, CAP_WIDTH = FONTS[LANG]
GIFS = ROOT / ("05_gif" if LANG == "zh" else f"05_gif_{LANG}")

FLOOD_THRESH = 90     # background flood-fill tolerance from pure white
ART_DARK = 150        # a pixel is "strong art" when its darkest channel is below this

CAP_H = int(WORK * 0.185)       # caption band height
SIDE_PAD = int(WORK * 0.035)
EDGE_PAD = int(WORK * 0.015)

# Transparency. Stickers must sit on WeChat's grey chat background with no white
# box, the way a published pack does. SENTINEL is a colour that appears nowhere in
# the artwork, so it survives quantisation as its own palette entry and can be
# named as the GIF's transparent index.
SENTINEL = (0, 255, 0)
RIM_PASSES = 3          # MaxFilter passes -> the white die-cut rim, in working px
RIM_KERNEL = 7

# (stride from 24fps, colours, gifsicle lossy level) - colour fidelity first,
# frame count second, lossy last.
LADDER = [
    (1, 200, 0), (1, 160, 0), (2, 160, 0), (2, 128, 30), (2, 96, 60),
    (3, 96, 60), (3, 80, 90), (4, 80, 90), (4, 64, 120), (5, 64, 120),
    (6, 48, 150), (6, 32, 180), (8, 32, 200), (10, 32, 220), (12, 24, 240),
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
        "-vf", f"fps={BASE_FPS},scale={WORK}:{WORK}:flags=lanczos",
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


def caption_band(pos):
    """(band_top, art_top, art_bottom) for a caption above or below the art."""
    if pos == "above":
        return EDGE_PAD, EDGE_PAD + CAP_H, WORK - EDGE_PAD
    return WORK - EDGE_PAD - CAP_H, EDGE_PAD, WORK - EDGE_PAD - CAP_H


def draw_caption(canvas, text, pos):
    """Black glyphs, white halo, black outer keyline - the standard 表情包
    caption treatment, readable against any chat background."""
    d = ImageDraw.Draw(canvas)
    font = fit_font(text, int(WORK * CAP_WIDTH), int(CAP_H * 0.86))
    band_top, _, _ = caption_band(pos)

    box = font.getbbox(text)
    tw, th = box[2] - box[0], box[3] - box[1]
    x = (WORK - tw) // 2 - box[0]
    y = band_top + (CAP_H - th) // 2 - box[1]

    size = font.size
    w_outer = max(3, round(size * 0.135))
    w_mid = max(2, round(size * 0.085))

    d.text((x, y), text, font=font, fill="black", stroke_width=w_outer, stroke_fill="black")
    d.text((x, y), text, font=font, fill="white", stroke_width=w_mid, stroke_fill="white")
    d.text((x, y), text, font=font, fill="black")
    return canvas


def sticker_alpha(canvas):
    """Opaque where the sticker is, transparent outside it.

    Flood-filling from the borders reaches the background *and* the model's own
    white die-cut border, since they are the same white and touch each other.
    Enclosed white - eye highlights, the caption's halo inside its black keyline -
    is never reached, which is exactly what we want to keep. Dilating what is left
    rebuilds the die-cut rim at a uniform width, so the visible edge is white
    meeting transparent and there is no dark fringe when the sticker is composited
    onto a coloured chat background.
    """
    tmp = canvas.copy()
    w, h = tmp.size
    for xy in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1),
               (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2)]:
        ImageDraw.floodfill(tmp, xy, SENTINEL, thresh=24)

    flat = Image.new("RGB", tmp.size, SENTINEL)
    art = ImageChops.difference(tmp, flat).convert("L").point(lambda v: 0 if v == 0 else 255)
    for _ in range(RIM_PASSES):
        art = art.filter(ImageFilter.MaxFilter(RIM_KERNEL))
    return art


def build_frames(sid, caption, pos="below"):
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

    _, art_top, art_bottom = caption_band(pos)
    zone_w, zone_h = WORK - 2 * SIDE_PAD, art_bottom - art_top
    scale = min(zone_w / bw, zone_h / bh)
    nw, nh = max(1, round(bw * scale)), max(1, round(bh * scale))
    ox = (WORK - nw) // 2
    # push the art against the caption so the pair reads as one unit
    oy = art_bottom - nh if pos == "below" else art_top

    out = []
    for im in cleaned:
        canvas = Image.new("RGB", (WORK, WORK), "white")
        canvas.paste(im.crop((x0, y0, x1, y1)).resize((nw, nh), Image.LANCZOS), (ox, oy))
        draw_caption(canvas, caption, pos)

        alpha = sticker_alpha(canvas)
        small = canvas.resize((FINAL, FINAL), Image.LANCZOS)
        # 1-bit alpha: GIF has no partial transparency, so threshold rather than
        # let LANCZOS produce a soft edge that would key badly
        mask = alpha.resize((FINAL, FINAL), Image.LANCZOS).point(lambda v: 255 if v >= 128 else 0)
        keyed = Image.composite(small, Image.new("RGB", small.size, SENTINEL), mask)
        out.append(keyed)
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

    # whichever palette slot the sentinel landed in becomes the transparent index
    table = pal.getpalette()
    tidx = min(range(len(table) // 3),
               key=lambda i: sum((table[i * 3 + c] - SENTINEL[c]) ** 2 for c in range(3)))

    q[0].save(dest, save_all=True, append_images=q[1:], duration=duration,
              loop=0, optimize=False, disposal=2, transparency=tidx)

    cmd = ["gifsicle", "-O3", "--no-warnings", f"--colors={colors}"]
    if lossy:
        cmd.append(f"--lossy={lossy}")
    cmd += ["-o", str(dest), str(dest)]
    run(cmd)
    return dest.stat().st_size, len(sel)


def save_thumb(frame, dest):
    """240x240 PNG thumbnail, transparent to match the GIF."""
    mask = ImageChops.difference(frame, Image.new("RGB", frame.size, SENTINEL)) \
        .convert("L").point(lambda v: 0 if v == 0 else 255)
    out = frame.convert("RGBA")
    out.putalpha(mask)
    out.save(dest, optimize=True)
    return dest.stat().st_size


def main():
    spec = json.loads((ROOT / "captions.json").read_text())
    GIFS.mkdir(exist_ok=True)
    FRAMES.mkdir(exist_ok=True)

    only = sys.argv[1:] or None
    report = []

    for s in spec["stickers"]:
        sid = s["id"]
        caption = s["caption"] if LANG == "zh" else s["caption_en"]
        if only and sid not in only:
            continue
        if not (VIDEO / f"{sid}.mp4").exists():
            print(f"{sid}  MISSING mp4")
            continue

        frames = build_frames(sid, caption, s.get("caption_pos", "below"))
        dest = GIFS / f"{sid}.gif"

        for stride, colors, lossy in LADDER:
            size, n = encode(frames, stride, colors, lossy, dest)
            if size <= SIZE_LIMIT:
                break

        thumb = GIFS / f"{sid}_thumb.png"
        save_thumb(frames[0], thumb)

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
