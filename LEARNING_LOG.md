# Learning log — WeChat sticker engine (表情包)

Append-only. Each entry is tagged with how strong the evidence is.

- **CONFIRMED** — directly observed in this repo's output, reproducible
- **MEASURED** — a number I computed, with the method stated
- **SOURCED** — from documentation or a vendor page
- **SUSPECTED** — a hypothesis I acted on but did not isolate

---

## 2026-08-04 — first build (ALLCPR 安安, 16 stickers)

### Video model choice is the whole ballgame for sticker work

**CONFIRMED.** PixVerse V6 (image2video, 720p, 3s) was given a chibi sticker on a
pure white background and an explicit "the background stays flat pure white and
empty" instruction. From roughly frame 10 onward it rendered the background
**solid black** with a vignette. Completely unusable for stickers, at any price.

**CONFIRMED.** Grok Imagine 1.5 on the identical start frame and identical prompt
held a flat pure-white background across the whole clip and kept the character
on-model. It costs 405 credits vs PixVerse's 50 — an 8× premium that is entirely
justified here, because the cheap output has zero salvage value.

*Rule: for any sticker or transparent/flat-background animation, bake off the
animator on ONE frame before spending the batch. Background integrity is not
something prompt wording can fix after the fact.*

### Grok drifts the camera even when told not to

**MEASURED.** Across the 16 clips I computed the non-white bounding box on 5
evenly spaced frames and compared its height. Zoom drift ranged **0.5% to 8.6%**
(median ~3%) despite "the camera is completely static and locked off, no zoom, no
pan" in every prompt. Three clips exceeded 7%.

Consequence: the character can creep toward the frame edge and clip. The fix that
worked was compositional, not generative — crop each clip to its own artwork
bounding box and rescale into a fixed art zone, which normalises framing regardless
of what the model did. Re-rolling the video would have been the expensive fix and
would not have guaranteed anything.

*Rule: assume a few percent of zoom drift from image2video and design the
compositor to absorb it. Don't pay to re-roll for framing.*

### Never ask an image model for empty space

**CONFIRMED.** The pose prompts said "with a clear empty white band across the
bottom fifth of the frame", intending to reserve room for a caption. Nano Banana
Pro interpreted this literally and **drew a rectangle** — a white box with a light
grey stroke, measured at RGB (196,196,196) with anti-aliased edges down to 165.
It appeared in roughly a third of the poses and survived into the GIFs as a visible
hairline.

Two-part fix, both needed: flood-fill the background from the borders (thresh 90),
then wipe pale neutral pixels (min channel ≥185, max−min ≤12). The neutrality test
is what makes it safe — real linework is either darker or clearly tinted, so the
certificate's grey ruled lines and the phone's grey body both survived.

*Rule: reserve layout space in the compositor, never in the prompt. Ask the model
only for the subject.*

### Typeset CJK in code, always

**CONFIRMED.** All 16 captions render perfectly because Pillow draws them from
Hiragino Sans GB W6 (`/System/Library/Fonts/Hiragino Sans GB.ttc`, **index 2** —
index 0 is W3 regular). Zero mangled characters, and captions are now editable in
`captions.json` without regenerating any art.

This is the same split already recorded for curio-static: the model paints, code
typesets.

The 表情包 caption treatment that reads correctly on any chat background is three
passes of the same glyphs: black stroke at ~0.135em, white stroke at ~0.085em,
then black fill. Black letters, white halo, black keyline.

### WeChat's real size ceiling is 100KB, not 500KB

**SOURCED.** The official 微信表情开放平台 bulletin says main sticker **240×240 GIF
≤100KB** and thumbnail **240×240 PNG ≤60KB**, 16 or 24 per set. Multiple
third-party tutorials (including recent ones) claim 500KB for the main image.
Building to 500KB would have meant a rejected submission.

*Rule: for platform specs, fetch the platform's own page. Blog posts drift.*

### What makes 100KB achievable

**MEASURED.** The combination that worked, in order of impact:

1. **One global palette, `dither=NONE`.** Flat cel art with no dithering
   compresses dramatically better and looks *cleaner*, not worse.
2. **A genuinely pure-white background.** Once compression noise around 252 was
   flattened to exactly 255, large runs compress to almost nothing.
3. **gifsicle `-O3 --lossy`.** Worth installing (`brew install gifsicle`).
4. **An encode ladder that drops frames before colours.** Colour banding on the
   blue hood is far more noticeable than a lower frame rate.

Final pack: all 16 between 76.5KB and 99.4KB, at **80–96 colours and 13–15 frames**.
An earlier ladder that cut colours first bottomed out at 32 colours and lossy=200
for the same file size — same budget, visibly worse art.

*Rule: at a fixed byte budget, spend on colours and starve the frame rate.*

---

## 2026-08-04 — publishing

### WeChat has no bulk sticker install, full stop

**SOURCED + CONFIRMED.** There is no import format for WeChat sticker packs — no
zip, no manifest, no deep link that installs a set into the sticker tray. One-tap
"添加" exists only for packs published in WeChat's own 表情商店 via the
表情开放平台. Telegram and LINE both have import flows; WeChat does not. So
"make it auto-add everything" is not an engineering problem, it is a submission
and review problem, and the honest answer is to say so rather than build a
convincing-looking installer that cannot work.

The manual route, which is what a download page can actually enable:
save image → send to 文件传输助手 → long-press → 添加到表情.

### Render re-encodes PNGs it serves

**MEASURED.** `site/assets/qr.png` is 734 bytes in git; the same file fetched from
`allcpr-stickers.onrender.com` is 684 bytes with a different md5. Decoding both and
diffing showed **zero pixel difference** across all 369×369 pixels — Render strips
PNG metadata on serve.

*Rule: never verify a deployed image asset by byte or hash comparison. Decode both
and diff the pixels, or you will chase a phantom corruption.*

### Deploying a static site from the API needs no OAuth for a public repo

**CONFIRMED.** `POST /v1/services` with `type: static_site`, an `ownerId`, a public
GitHub repo URL, and `serviceDetails.publishPath` creates and deploys the site with
no GitHub connection step. First deploy went live in about ten seconds, and
`autoDeploy: yes` picks up every subsequent push to `master`.

Watch the response shape when polling: `/deploys` returns a **list of
`{deploy: {...}, cursor}` wrappers**, not a list of deploys. Indexing straight to
`[0]['status']` silently yields nothing and looks like a stuck deploy.

---

## 2026-08-04 — transparency, 24 stickers, and a second language

### Typesetting in code makes translation free

**CONFIRMED.** A complete 24-sticker English set cost **zero** image or video
generation. Because captions are drawn by Pillow rather than the image model, the
same 24 animations were recomposited with `caption_en` and a Latin face. A third
language is one dictionary entry per sticker plus a re-run.

This is the compounding payoff of the earlier "model paints, code typesets" rule:
it started as a correctness fix for mangled Chinese glyphs, and it turned out to
be what makes the pack localisable at all.

Font pairing that holds the same weight across scripts: Hiragino Sans GB **W6**
for Chinese, **Arial Black** for English. Both carry the three-pass treatment
(black stroke, white halo, black fill) without going muddy at 240px.

### Transparency is the difference between a sticker and a white box

**CONFIRMED.** Published WeChat packs are transparent; they sit directly on the
chat background. An opaque sticker shows as a white rectangle on WeChat's grey
(#EDEDED) and reads instantly as amateur. This was the largest visual gap against
the reference pack and was not something the size or caption work could hide.

The keying technique that works on flat cel art with a die-cut border:

1. Flood-fill from the borders. This reaches the background **and** the model's
   own white die-cut border, because they are the same white and touch.
2. Enclosed white is never reached — eye highlights, and critically the caption's
   white halo inside its black keyline — so those stay opaque, which is what keeps
   the caption legible on any background.
3. Dilate what remains (3 × MaxFilter(7)) to rebuild the die-cut rim at a uniform
   width. The visible edge is then **white meeting transparent**, so there is no
   dark fringe when composited onto a coloured background.

Step 3 is the one that matters. Keying white directly to transparent leaves the
black outline anti-aliased against white, and every sticker gets a pale halo.

Cost: transparency plus `disposal=2` weakens inter-frame compression, so the pack
settled at 8–13 frames and 64–80 colours instead of 13–15 frames and 80–96. Worth
it — a white box is a worse defect than a slightly lower frame rate.

### PIL's ImageSequence.Iterator silently destroys the info you are about to check

**CONFIRMED, and it cost a full false alarm.** This verifier reported all 48
stickers as opaque:

```python
im = Image.open(path)
frames = sum(1 for _ in ImageSequence.Iterator(im))   # seeks to the LAST frame
transparent = im.info.get("transparency") is not None  # reads the last frame's info
```

Iterating **mutates** `im` by seeking, and the final frame's `info` dict does not
carry the `transparency` key. Every sticker was in fact transparent. Read `size`,
`loop` and `transparency` off frame 0 *before* iterating, or re-open the file.

*Rule: in PIL, treat any multi-frame image as stateful. Harvest metadata first,
iterate second.*

### Compare byte counts, not rounded kilobytes

**MEASURED.** The gate is 100,000 bytes. The largest English GIF is 99,950 bytes —
which `round(n/1000, 1)` renders as `100.0KB`, indistinguishable from a violation.
The check now compares raw bytes and only the display rounds.

### Extract only the frames the ladder can use

**MEASURED.** Frames were being extracted at the source 24fps, but the encode
ladder never selects more than half of them. Extracting at 12fps up front halved
the per-frame flood-fill cost, taking a 24-sticker build from ~12 minutes to ~6,
and — because the stride arithmetic changed — several stickers landed on *more*
colours than before at the same file size.
