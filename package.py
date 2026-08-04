#!/usr/bin/env python3
"""Assemble the WeChat submission folders (Chinese and English), the detail
banners, and a preview sheet per language."""

import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageSequence

ROOT = Path(__file__).parent
OUT = ROOT / "06_deliverable"

FONT = "/System/Library/Fonts/Hiragino Sans GB.ttc"
LATIN = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
BLUE = (0, 160, 233)
CHAT = (237, 237, 237)      # WeChat chat grey, so transparency is visible

LANGS = {
    "zh": {"dir": ROOT / "05_gif",    "main": "01_主图_main_gif",
           "thumb": "02_缩略图_thumbnail_png", "key": "caption",
           "title": "安安", "sub": "人人都应学 CPR", "sheet": "微信表情包 · 24 枚 · 240x240 GIF"},
    "en": {"dir": ROOT / "05_gif_en", "main": "01_main_gif",
           "thumb": "02_thumbnail_png", "key": "caption_en",
           "title": "An An", "sub": "All of us should learn CPR",
           "sheet": "WeChat sticker pack · 24 stickers · 240x240 GIF"},
}


def font(size, latin=False):
    return ImageFont.truetype(LATIN if latin else FONT, size,
                              index=0 if latin else 2)


def build_banner(lang, cfg, dest):
    """详情页横幅 - 750x400 PNG."""
    W, H = 750, 400
    im = Image.new("RGB", (W, H), (240, 249, 255))
    d = ImageDraw.Draw(im)
    d.rectangle([0, H - 10, W, H], fill=BLUE)

    hero = Image.open(cfg["dir"] / "12.gif").convert("RGBA")
    bg = Image.new("RGBA", hero.size, (240, 249, 255, 255))
    hero = Image.alpha_composite(bg, hero).convert("RGB")
    hero.thumbnail((330, 330), Image.LANCZOS)
    im.paste(hero, (34, (H - hero.height) // 2 - 6))

    x = 380
    d.text((x, 118), "ALLCPR", font=font(64, latin=True), fill=BLUE)
    d.text((x, 192), cfg["title"], font=font(60, latin=(lang == "en")), fill=(28, 28, 30))
    d.text((x, 274), cfg["sub"], font=font(26, latin=(lang == "en")), fill=(90, 100, 110))

    logo = Image.open(ROOT / "00_ref" / "allcpr_logo_full.png").convert("RGB")
    logo.thumbnail((92, 92), Image.LANCZOS)
    im.paste(logo, (W - 122, H - 130))

    im.save(dest, optimize=True)
    return dest.stat().st_size


def build_preview(lang, cfg, spec, dest):
    """Contact sheet on chat grey, so the transparency is visible at a glance."""
    C, COLS = 240, 6
    rows = (len(spec["stickers"]) + COLS - 1) // COLS
    head = 92
    im = Image.new("RGB", (C * COLS, head + C * rows), CHAT)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, im.width, head], fill=(240, 249, 255))
    d.text((26, 18), f"ALLCPR {cfg['title']}", font=font(38, latin=(lang == "en")), fill=BLUE)
    d.text((26, 62), cfg["sheet"], font=font(20, latin=(lang == "en")), fill=(90, 100, 110))

    for n, s in enumerate(spec["stickers"]):
        g = Image.open(cfg["dir"] / f"{s['id']}.gif").convert("RGBA")
        cell = Image.new("RGBA", g.size, CHAT + (255,))
        im.paste(Image.alpha_composite(cell, g).convert("RGB"),
                 ((n % COLS) * C, head + (n // COLS) * C))
    im.save(dest, optimize=True)
    return dest.stat().st_size


def main():
    spec = json.loads((ROOT / "captions.json").read_text())
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    report, problems = {}, []
    for lang, cfg in LANGS.items():
        main_dir = OUT / lang / cfg["main"]
        thumb_dir = OUT / lang / cfg["thumb"]
        main_dir.mkdir(parents=True)
        thumb_dir.mkdir(parents=True)

        rows = []
        for s in spec["stickers"]:
            sid = s["id"]
            g, t = cfg["dir"] / f"{sid}.gif", cfg["dir"] / f"{sid}_thumb.png"
            shutil.copy(g, main_dir / f"{sid}.gif")
            shutil.copy(t, thumb_dir / f"{sid}.png")

            im = Image.open(g)
            frames = sum(1 for _ in ImageSequence.Iterator(im))
            row = {
                "id": sid, "caption": s[cfg["key"]],
                "gif_kb": round(g.stat().st_size / 1000, 1),
                "thumb_kb": round(t.stat().st_size / 1000, 1),
                "size": f"{im.size[0]}x{im.size[1]}", "frames": frames,
                "loop_forever": im.info.get("loop") == 0,
                "transparent": im.info.get("transparency") is not None,
            }
            rows.append(row)
            if (row["gif_kb"] > 100 or row["thumb_kb"] > 60 or row["size"] != "240x240"
                    or not row["loop_forever"] or row["frames"] < 2 or not row["transparent"]):
                problems.append(f"{lang}/{sid}: {row}")

        banner = build_banner(lang, cfg, OUT / lang / f"03_banner_750x400_{lang}.png")
        preview = build_preview(lang, cfg, spec, OUT / lang / f"04_preview_{lang}.png")
        report[lang] = {"stickers": rows, "banner_bytes": banner, "preview_bytes": preview}
        print(f"{lang}: {len(rows)} stickers, banner {banner/1000:.1f}KB, "
              f"preview {preview/1000:.1f}KB, "
              f"gif {min(r['gif_kb'] for r in rows)}-{max(r['gif_kb'] for r in rows)}KB")

    (OUT / "manifest.json").write_text(
        json.dumps({"pack": spec["pack"], "languages": report}, ensure_ascii=False, indent=2))

    print(f"\nspec violations: {len(problems)}")
    for p in problems:
        print("  ", p)


if __name__ == "__main__":
    main()
