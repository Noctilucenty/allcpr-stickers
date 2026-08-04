# ALLCPR 安安 — 微信表情包 / WeChat sticker pack

**Live: https://allcpr-stickers.onrender.com**

24 animated stickers for ALLCPR, in two full language sets — Chinese and English —
built the same way the TEEC pack works: one chibi mascot, one costume, one caption
per sticker, transparent background.

The mascot is **安安** (An An, from 安全 / safety). He wears the ALLCPR logo mark
itself — the blue chevron "A" with the red heart at its apex — as a plush hood,
the same move TEEC makes with the Tsinghua gate.

## The 24 stickers

| # | 中文 | English | Scene |
|---|------|---------|-------|
| 01 | 收到 | Got it | Salute |
| 02 | 我来 | I'm on it | Rolling up a sleeve |
| 03 | 别慌 | Stay calm | Calming raised palm |
| 04 | 快打911 | Call 911 | Pointing at a phone |
| 05 | 用力按压 | Push hard | Compressions on a training manikin |
| 06 | 学会啦 | Now I know | Lightbulb moment |
| 07 | 拿证啦 | Certified! | Holding up the certificate |
| 08 | 开课啦 | Class time | Handbell with an AED case |
| 09 | 加油 | You got this | Megaphone |
| 10 | 棒棒哒 | Awesome | Arms up, stars |
| 11 | 点赞 | Nice one | Thumbs up, wink |
| 12 | 比心 | Love it | Finger hearts |
| 13 | 谢谢 | Thank you | Bowing |
| 14 | 辛苦了 | Great work | Offering tea |
| 15 | 救命啊 | Help! | Comic panic |
| 16 | 生日快乐 | Happy Birthday | Cake with a candle |
| 17 | 安全第一 | Safety first | Protective palm, shield glow |
| 18 | 没问题 | No problem | OK sign, wink |
| 19 | 稍等 | One sec | One finger up, hourglass |
| 20 | 满员啦 | All full | Clipboard of green checks |
| 21 | 早上好 | Good morning | Morning stretch, sun |
| 22 | 晚安 | Good night | Asleep with a pillow and moon |
| 23 | 恭喜恭喜 | Congrats! | Congratulation salute, firecrackers |
| 24 | 我在 | I'm here | Arm shot up to volunteer |

Captions 04, 05 and 15 are the ones that make it an ALLCPR pack rather than a
generic cute pack — the actual chain of survival, played for laughs.

Eight of the 24 put the caption above the character instead of below, the way the
TEEC pack varies it.

## Two languages for free

Captions are typeset in code with Pillow, never drawn by the image model. That
means a second language costs **no image or video generation at all** — the same
animations are recomposited with different text. Adding a third language is one
dictionary entry per sticker and a re-run.

The Chinese set uses Hiragino Sans GB W6; the English set uses Arial Black, which
carries the same heavy 表情包 weight in Latin.

## What's in `06_deliverable/`

```
zh/01_主图_main_gif/       01.gif … 24.gif     240×240 GIF, ≤100KB, transparent, loops
zh/02_缩略图_thumbnail_png/ 01.png … 24.png     240×240 PNG, ≤60KB, transparent
zh/03_banner_750x400_zh.png                     detail-page banner
zh/04_preview_zh.png                            contact sheet on chat grey
en/…                                            the same set in English
manifest.json                                   per-sticker size, frames, loop, transparency
```

Every file is checked against the spec programmatically; `package.py` reports
`spec violations: 0`.

## Why there is no one-tap "add all"

WeChat only offers one-tap install of a whole pack for stickers published in its
own 表情商店. There is no supported way to bulk-install stickers into the sticker
tray from a web page, a zip, or a file of any kind — WeChat has no import format
the way Telegram and LINE do.

So there are exactly two routes:

- **Now** — people save each GIF and add it from a chat. The site walks them
  through it on phone and desktop; roughly ten seconds a sticker.
- **One tap** — submit the pack to the 表情开放平台 and get it published. After
  approval it installs in a single tap and the store gives you a share link and QR.

The assets for that submission are built and spec-compliant, so what remains is
account registration, the IP declaration, and review.

## Hosting

| | |
|---|---|
| URL | https://allcpr-stickers.onrender.com |
| Service | `srv-d9p5v8r7uimc73al6gig` (Render static site) |
| Repo | `Noctilucenty/allcpr-stickers`, branch `master` |
| Publish path | `site/` |
| Auto-deploy | on every push to `master` |

The Render API key lives in `.env`, which is gitignored and not in this repo.

## Rebuilding

```bash
LANG_SET=zh python3 build_stickers.py        # Chinese set, all 24
LANG_SET=en python3 build_stickers.py        # English set
LANG_SET=zh python3 build_stickers.py 05 12  # just these
python3 package.py                           # assemble 06_deliverable/
python3 build_site.py                        # regenerate site/
```

Run the two language sets **sequentially** — they share `04_frames/`.

To change a caption, edit `captions.json` (`caption` / `caption_en`) and re-run.
Changing a *pose* means regenerating that sticker's art and animation.

## How it was made

| Stage | Tool |
|-------|------|
| Mascot design + 24 poses | OpenArt · Nano Banana Pro (image2image, 2K, logo as reference) |
| Animation | OpenArt · Grok Imagine 1.5 (image2video, 1:1, 720p, 3s) |
| Background removal, captions, layout | Pillow |
| GIF encode + size optimisation | ffmpeg + gifsicle |

`build_stickers.py` flood-fills the background to white, isolates the real artwork
by outline darkness, crops and rescales it into a fixed art zone beside a reserved
caption band, rebuilds the die-cut rim as a uniform dilation so the transparent
edge has no dark fringe, then walks an encode ladder — dropping frames and colours
in that order — until each GIF fits under 100KB.

See `LEARNING_LOG.md` for what broke along the way and the rules that came out of it.
