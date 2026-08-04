# ALLCPR 安安 — 微信表情包

**Live: https://allcpr-stickers.onrender.com**

A 16-sticker animated WeChat sticker pack for ALLCPR, built the same way the TEEC
pack works: one chibi mascot, one costume, one caption per sticker.

The mascot is **安安** (An An, from 安全 / safety). He wears the ALLCPR sky-blue
onesie and, in place of TEEC's Tsinghua gate hat, the ALLCPR logo mark itself —
the blue chevron "A" with the red heart at its apex — as a plush hood.

## The 16 stickers

| # | Caption | Meaning | Scene |
|---|---------|---------|-------|
| 01 | 收到 | Got it | Salute |
| 02 | 我来 | I'll take it | Rolling up a sleeve |
| 03 | 别慌 | Don't panic | Calming raised palm |
| 04 | 快打911 | Call 911 | Pointing at a phone |
| 05 | 用力按压 | Push hard | Compressions on a training manikin |
| 06 | 学会啦 | I've got it | Lightbulb moment |
| 07 | 拿证啦 | Certified | Holding up the certificate |
| 08 | 开课啦 | Class is starting | Handbell with an AED case |
| 09 | 加油 | Keep it up | Megaphone |
| 10 | 棒棒哒 | Awesome | Arms up, stars |
| 11 | 点赞 | Nice one | Thumbs up, wink |
| 12 | 比心 | Love it | Finger hearts |
| 13 | 谢谢 | Thank you | Bowing |
| 14 | 辛苦了 | Thanks for your hard work | Offering tea |
| 15 | 救命啊 | Help | Comic panic |
| 16 | 生日快乐 | Happy birthday | Cake with a candle |

Captions 04, 05 and 15 are the ones that make it an ALLCPR pack rather than a
generic cute pack — they are the actual chain of survival, played for laughs.

## What's in `06_deliverable/`

| Folder | Contents | Spec |
|--------|----------|------|
| `01_主图_main_gif/` | `01.gif` … `16.gif` | 240×240 GIF, all ≤100KB, loop forever |
| `02_缩略图_thumbnail_png/` | `01.png` … `16.png` | 240×240 PNG, all ≤60KB |
| `03_详情页横幅_banner_750x400.png` | Detail-page banner | 750×400 PNG, 51KB |
| `04_预览_preview_all16.png` | Contact sheet of the whole pack | internal review only |
| `manifest.json` | Per-sticker size, frame count, loop flag | verification record |

Every file was checked against the spec programmatically; `package.py` reports
`spec violations: 0`.

## Why there is no one-tap "add all"

WeChat only offers one-tap install of a whole pack for stickers published in its
own 表情商店. There is no supported way to bulk-install stickers into the sticker
tray from a web page, a zip, or a file of any kind — WeChat has no import format
the way Telegram and LINE do. Anything claiming otherwise is either a screen
recording of the manual flow or a repackaged store link.

So there are exactly two routes:

- **Now** — people save each GIF and add it from a chat. The site walks them
  through it; roughly ten seconds a sticker, two minutes for all sixteen.
- **One tap** — submit the pack to the 表情开放平台 and get it published. After
  approval it appears in the sticker store and installs in a single tap, and the
  store gives you a share link and QR that install the whole pack directly.

The assets for that submission are already built and spec-compliant, so the
remaining work is account registration, the IP declaration, and review.

## Hosting

The public page is a Render static site, deployed from this repo:

| | |
|---|---|
| URL | https://allcpr-stickers.onrender.com |
| Service | `srv-d9p5v8r7uimc73al6gig` (static site, workspace "My Workspace") |
| Repo | `Noctilucenty/allcpr-stickers`, branch `master` |
| Publish path | `site/` |
| Auto-deploy | on every push to `master` |

`build_site.py` regenerates `site/` — the page, the 16 GIFs, the zip, and the QR
code. Push and Render redeploys itself. The Render API key lives in `.env`, which
is gitignored; it is not in this repo.

## Submitting to WeChat

The official spec is on the [微信表情开放平台](https://sticker.weixin.qq.com):
main sticker **240×240 GIF, ≤100KB**; thumbnail **240×240 PNG, ≤60KB**; a set must
contain **16 or 24** stickers. Note that several third-party guides quote 500KB for
the main image — that is out of date, so this pack is built to the stricter 100KB.

Submission needs a registered designer account on the platform and a declaration
that the artwork is original IP. The pack is original: the mascot was designed for
this project and the only brand element carried over is ALLCPR's own logo mark.

## Using it right now, without submitting

The GIFs work as-is in any WeChat chat. Send one, long-press it, and choose
**添加到表情** to keep it in your sticker tray. That is the fastest way to get these
into the ALLCPR group chats today; platform submission is only needed if you want
the pack publicly listed in WeChat's sticker store.

## Rebuilding

```bash
python3 build_stickers.py          # all 16
python3 build_stickers.py 05 12    # just these
python3 package.py                 # re-assemble 06_deliverable/
```

To change a caption, edit `captions.json` and re-run — the Chinese is typeset by
Pillow from the system font, never drawn by the image model, so it is always
correct. Changing a *pose* means regenerating that sticker's art and animation.

## How it was made

| Stage | Tool |
|-------|------|
| Mascot design + 16 poses | OpenArt · Nano Banana Pro (image2image, 2K, logo as reference) |
| Animation | OpenArt · Grok Imagine 1.5 (image2video, 1:1, 720p, 3s) |
| Background cleanup, captions, layout | Pillow |
| GIF encode + size optimisation | ffmpeg + gifsicle |

`build_stickers.py` flood-fills the background to pure white, isolates the real
artwork by outline darkness, crops and rescales it into a fixed art zone above a
reserved caption band, then walks an encode ladder — dropping frames and colours
in that order — until each GIF fits under 100KB. Most landed at 80–96 colours and
13–15 frames.
