#!/usr/bin/env python3
"""Assemble the WeChat submission folder, the detail banner, and a preview sheet."""

import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageSequence

ROOT = Path(__file__).parent
GIFS = ROOT / "05_gif"
OUT = ROOT / "06_deliverable"

FONT = "/System/Library/Fonts/Hiragino Sans GB.ttc"
BOLD, REG = 2, 0
BLUE = (0, 160, 233)
RED = (227, 6, 19)


def font(size, idx=BOLD):
    return ImageFont.truetype(FONT, size, index=idx)


def centred(d, xy, text, f, fill):
    b = f.getbbox(text)
    d.text((xy[0] - (b[2] - b[0]) / 2 - b[0], xy[1] - (b[3] - b[1]) / 2 - b[1]),
           text, font=f, fill=fill)


def build_banner(spec, dest):
    """详情页横幅 - 750x400 PNG."""
    W, H = 750, 400
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)

    d.rectangle([0, 0, W, H], fill=(240, 249, 255))
    d.rectangle([0, H - 10, W, H], fill=BLUE)

    hero = Image.open(GIFS / "12.gif").convert("RGB")
    hero.thumbnail((330, 330), Image.LANCZOS)
    im.paste(hero, (34, (H - hero.height) // 2 - 6))

    x = 380
    d.text((x, 118), "ALLCPR", font=font(64), fill=BLUE)
    d.text((x, 190), "安安", font=font(64), fill=(28, 28, 30))
    d.text((x, 272), "人人都应学 CPR", font=font(30), fill=(90, 100, 110))

    logo = Image.open(ROOT / "00_ref" / "allcpr_logo_full.png").convert("RGB")
    logo.thumbnail((92, 92), Image.LANCZOS)
    im.paste(logo, (W - 122, H - 130))

    im.save(dest, optimize=True)
    return dest.stat().st_size


def build_preview(spec, dest):
    """Contact sheet of all 16 for internal review."""
    C, COLS = 240, 4
    rows = (len(spec["stickers"]) + COLS - 1) // COLS
    head = 92
    im = Image.new("RGB", (C * COLS, head + C * rows), "white")
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, im.width, head], fill=(240, 249, 255))
    d.text((26, 20), "ALLCPR 安安", font=font(38), fill=BLUE)
    d.text((26, 62), "微信表情包 · 16 枚 · 240x240 GIF", font=font(20), fill=(90, 100, 110))

    for n, s in enumerate(spec["stickers"]):
        g = Image.open(GIFS / f"{s['id']}.gif").convert("RGB")
        im.paste(g, ((n % COLS) * C, head + (n // COLS) * C))
    im.save(dest, optimize=True)
    return dest.stat().st_size


def main():
    spec = json.loads((ROOT / "captions.json").read_text())
    if OUT.exists():
        shutil.rmtree(OUT)
    main_dir = OUT / "01_主图_main_gif"
    thumb_dir = OUT / "02_缩略图_thumbnail_png"
    for p in (main_dir, thumb_dir):
        p.mkdir(parents=True)

    rows = []
    for s in spec["stickers"]:
        sid = s["id"]
        g = GIFS / f"{sid}.gif"
        t = GIFS / f"{sid}_thumb.png"
        shutil.copy(g, main_dir / f"{sid}.gif")
        shutil.copy(t, thumb_dir / f"{sid}.png")

        im = Image.open(g)
        frames = sum(1 for _ in ImageSequence.Iterator(im))
        loops = im.info.get("loop", None)
        rows.append({
            "id": sid, "caption": s["caption"],
            "gif_kb": round(g.stat().st_size / 1000, 1),
            "thumb_kb": round(t.stat().st_size / 1000, 1),
            "size": f"{im.size[0]}x{im.size[1]}",
            "frames": frames, "loop_forever": loops == 0,
        })

    banner = build_banner(spec, OUT / "03_详情页横幅_banner_750x400.png")
    preview = build_preview(spec, OUT / "04_预览_preview_all16.png")

    (OUT / "manifest.json").write_text(
        json.dumps({"pack": spec["pack"], "stickers": rows,
                    "banner_bytes": banner, "preview_bytes": preview},
                   ensure_ascii=False, indent=2))

    bad = [r for r in rows if r["gif_kb"] > 100 or r["thumb_kb"] > 60
           or r["size"] != "240x240" or not r["loop_forever"] or r["frames"] < 2]
    print(f"{len(rows)} stickers packaged")
    print(f"banner {banner/1000:.1f}KB   preview {preview/1000:.1f}KB")
    print(f"spec violations: {len(bad)}")
    for b in bad:
        print("  ", b)


if __name__ == "__main__":
    main()
