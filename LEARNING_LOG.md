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
