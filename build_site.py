#!/usr/bin/env python3
"""Build the public static site that gets served from Render.

Unlike the self-contained artifact page, this one references real .gif files:
long-press-to-save is more reliable against a real URL than a data URI, and the
page loads progressively instead of shipping 5MB up front.
"""

import json
import shutil
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).parent
DELIV = ROOT / "06_deliverable"
GIFDIR = DELIV / "01_主图_main_gif"
THUMBDIR = DELIV / "02_缩略图_thumbnail_png"
SITE = ROOT / "site"

spec = json.loads((ROOT / "captions.json").read_text())
stickers = spec["stickers"]

# ---------------------------------------------------------------- files
if SITE.exists():
    shutil.rmtree(SITE)
(SITE / "stickers").mkdir(parents=True)
(SITE / "assets").mkdir(parents=True)

for s in stickers:
    shutil.copy(GIFDIR / f"{s['id']}.gif", SITE / "stickers" / f"{s['id']}.gif")

logo = Image.open(ROOT / "00_ref" / "allcpr_logo_full.png").convert("RGB")
logo.thumbnail((160, 160), Image.LANCZOS)
logo.save(SITE / "assets" / "allcpr-logo.png", optimize=True)

shutil.copy(DELIV / "03_详情页横幅_banner_750x400.png", SITE / "assets" / "banner.png")

# QR code - how a link actually gets passed around in a WeChat group.
# Black on white at high error correction so it survives a phone screenshot.
SITE_URL = "https://allcpr-stickers.onrender.com"
import segno
segno.make(SITE_URL, error="h").save(
    SITE / "assets" / "qr.png", scale=9, border=2, dark="#0F2230", light="#FFFFFF")

# one zip holding everything a submitter or a user would want
zip_path = SITE / "allcpr-anan-stickers.zip"
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for s in stickers:
        sid, cap = s["id"], s["caption"]
        z.write(GIFDIR / f"{sid}.gif", f"主图_main/{sid}_{cap}.gif")
        z.write(THUMBDIR / f"{sid}.png", f"缩略图_thumbnail/{sid}_{cap}.png")
    z.write(DELIV / "03_详情页横幅_banner_750x400.png", "详情页横幅_banner_750x400.png")
zip_kb = round(zip_path.stat().st_size / 1024)

# ---------------------------------------------------------------- markup
tiles = "\n".join(
    f"""      <figure class="tile">
        <div class="art"><img src="stickers/{s['id']}.gif" alt="{s['caption']}" width="240" height="240" loading="lazy"></div>
        <figcaption>
          <span class="cap">{s['caption']}</span>
          <a class="save" href="stickers/{s['id']}.gif" download="ALLCPR_{s['id']}_{s['caption']}.gif">保存</a>
        </figcaption>
      </figure>"""
    for s in stickers
)

HTML = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>ALLCPR 安安 · 微信表情包</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="ALLCPR 安安 微信表情包，16 枚会动的 GIF，免费下载。">
<meta property="og:title" content="ALLCPR 安安 · 微信表情包">
<meta property="og:description" content="16 枚会动的 GIF，收到、加油、辛苦了，还有快打911、用力按压。">
<meta property="og:image" content="assets/banner.png">
<link rel="icon" href="assets/allcpr-logo.png">
<style>
  :root {{
    --blue:#00A0E9; --blue-ink:#0076AE; --wash:#EAF6FE; --red:#E30613;
    --paper:#EEF5FA; --ink:#0F2230; --muted:#4A6675; --line:#D6E4EE;
    --shadow:0 1px 2px rgba(15,34,48,.06), 0 8px 20px rgba(15,34,48,.06);
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --blue:#3FBDF7; --blue-ink:#8AD6FB; --wash:#132735; --red:#FF5A63;
      --paper:#0B1621; --ink:#E9F2F8; --muted:#94AFC1; --line:#1D3243;
      --shadow:0 1px 2px rgba(0,0,0,.4), 0 10px 26px rgba(0,0,0,.34);
    }}
  }}
  :root[data-theme="light"] {{
    --blue:#00A0E9; --blue-ink:#0076AE; --wash:#EAF6FE; --red:#E30613;
    --paper:#EEF5FA; --ink:#0F2230; --muted:#4A6675; --line:#D6E4EE;
    --shadow:0 1px 2px rgba(15,34,48,.06), 0 8px 20px rgba(15,34,48,.06);
  }}
  :root[data-theme="dark"] {{
    --blue:#3FBDF7; --blue-ink:#8AD6FB; --wash:#132735; --red:#FF5A63;
    --paper:#0B1621; --ink:#E9F2F8; --muted:#94AFC1; --line:#1D3243;
    --shadow:0 1px 2px rgba(0,0,0,.4), 0 10px 26px rgba(0,0,0,.34);
  }}

  * {{ box-sizing:border-box; }}
  html {{ -webkit-text-size-adjust:100%; }}
  body {{
    margin:0; background:var(--paper); color:var(--ink);
    font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB",
                "Microsoft YaHei","Segoe UI",system-ui,sans-serif;
    font-size:16px; line-height:1.65; -webkit-font-smoothing:antialiased;
  }}
  .wrap {{ max-width:960px; margin:0 auto; padding:0 20px 72px; }}

  header {{
    display:flex; align-items:center; gap:20px; flex-wrap:wrap;
    padding:36px 0 28px; border-bottom:1px solid var(--line);
  }}
  .hero {{
    width:104px; height:104px; flex:none; border-radius:20px; background:#fff;
    box-shadow:var(--shadow); overflow:hidden;
  }}
  .hero img {{ display:block; width:100%; height:100%; object-fit:contain; }}
  .titles {{ flex:1 1 240px; min-width:0; }}
  h1 {{ margin:0; font-size:clamp(28px,5vw,40px); font-weight:900; letter-spacing:-.02em; text-wrap:balance; }}
  h1 .en {{ color:var(--blue); }}
  .sub {{ margin:6px 0 0; color:var(--muted); font-size:15px; }}
  .brandmark {{ width:44px; height:44px; border-radius:50%; flex:none; opacity:.9; }}

  .lede {{ margin:26px 0 0; max-width:62ch; color:var(--muted); }}
  .lede strong {{ color:var(--ink); font-weight:600; }}
  .heart {{ color:var(--red); }}

  .callout {{
    margin:26px 0 0; padding:18px 22px; border-radius:14px;
    background:var(--wash); border:1px solid var(--line);
    border-left:4px solid var(--blue);
  }}
  .callout h3 {{ margin:0 0 6px; font-size:16px; font-weight:800; }}
  .callout p {{ margin:0; font-size:15px; color:var(--muted); max-width:62ch; }}

  .grab {{ margin:22px 0 0; display:flex; align-items:center; gap:16px; flex-wrap:wrap; }}
  .btn {{
    display:inline-block; background:var(--blue); color:#fff; font-weight:700;
    text-decoration:none; padding:13px 24px; border-radius:10px; font-size:16px;
    transition:transform .15s ease, filter .15s ease;
  }}
  .btn:hover {{ filter:brightness(1.06); transform:translateY(-1px); }}
  .btn:focus-visible, .save:focus-visible {{ outline:3px solid var(--blue-ink); outline-offset:3px; }}
  .grab p {{ margin:0; font-size:14px; color:var(--muted); }}

  h2 {{ margin:52px 0 0; font-size:13px; font-weight:700; letter-spacing:.14em; text-transform:uppercase; color:var(--blue-ink); }}
  h2 + .note {{ margin-top:8px; color:var(--muted); font-size:14px; }}

  .tracks {{ display:grid; gap:20px; grid-template-columns:1fr 1fr; margin-top:20px; }}
  @media (max-width:660px) {{ .tracks {{ grid-template-columns:1fr; }} }}
  .track {{ background:var(--wash); border:1px solid var(--line); border-radius:14px; padding:22px 24px; }}
  .track h3 {{ margin:0 0 14px; font-size:17px; font-weight:800; }}
  ol {{ margin:0; padding:0; list-style:none; counter-reset:step; display:grid; gap:12px; }}
  ol li {{ counter-increment:step; display:grid; grid-template-columns:26px 1fr; gap:12px; align-items:start; }}
  ol li::before {{
    content:counter(step); width:26px; height:26px; border-radius:50%;
    background:var(--blue); color:#fff; font-size:13px; font-weight:800;
    display:grid; place-items:center; font-variant-numeric:tabular-nums;
  }}
  kbd {{
    font:inherit; font-weight:700; background:#fff; color:#0F2230;
    border:1px solid var(--line); border-radius:6px; padding:1px 7px; white-space:nowrap;
  }}
  ol li em {{ display:inline-block; margin-top:6px; font-style:normal; font-size:13.5px; color:var(--muted); }}

  .share {{
    margin-top:28px; display:flex; align-items:center; gap:22px; flex-wrap:wrap;
    background:var(--wash); border:1px solid var(--line); border-radius:14px; padding:20px 22px;
  }}
  .share img {{ width:118px; height:118px; flex:none; border-radius:10px; background:#fff; padding:6px; }}
  .share div {{ flex:1 1 220px; min-width:0; }}
  .share h3 {{ margin:0 0 6px; font-size:16px; font-weight:800; }}
  .share p {{ margin:0; font-size:14px; color:var(--muted); }}
  .share code {{
    display:inline-block; margin-top:8px; font-size:13px; word-break:break-all;
    background:#fff; color:#0F2230; border:1px solid var(--line);
    border-radius:6px; padding:3px 9px;
  }}

  .grid {{ margin-top:20px; display:grid; gap:16px; grid-template-columns:repeat(4,1fr); }}
  @media (max-width:860px) {{ .grid {{ grid-template-columns:repeat(3,1fr); }} }}
  @media (max-width:600px) {{ .grid {{ grid-template-columns:repeat(2,1fr); }} }}
  .tile {{ margin:0; border-radius:14px; overflow:hidden; box-shadow:var(--shadow); background:#fff; }}
  .art {{ background:#fff; }}
  .art img {{ display:block; width:100%; height:auto; }}
  figcaption {{
    display:flex; align-items:center; justify-content:space-between; gap:8px;
    padding:10px 12px; background:#fff; border-top:1px solid #E8EEF3;
  }}
  .cap {{ font-weight:700; font-size:15px; color:#0F2230; }}
  .save {{
    font-size:13px; font-weight:700; color:#0076AE; text-decoration:none;
    border:1px solid #D6E4EE; border-radius:7px; padding:3px 10px; background:#fff;
  }}
  .save:hover {{ background:#EAF6FE; }}

  footer {{ margin-top:56px; padding-top:24px; border-top:1px solid var(--line); color:var(--muted); font-size:14px; }}
  footer p {{ margin:0 0 8px; max-width:66ch; }}
  footer a {{ color:var(--blue-ink); }}

  @media (prefers-reduced-motion: reduce) {{ * {{ transition:none !important; }} }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="hero"><img src="stickers/12.gif" alt="安安" width="240" height="240"></div>
    <div class="titles">
      <h1><span class="en">ALLCPR</span> 安安</h1>
      <p class="sub">微信表情包 · 16 枚 · 会动的 GIF</p>
    </div>
    <img class="brandmark" src="assets/allcpr-logo.png" alt="ALLCPR" width="44" height="44">
  </header>

  <p class="lede">安安戴的是 ALLCPR 的标志——蓝色的 A 里面一颗<span class="heart">红心</span>。
  这套表情是给 ALLCPR 的同事和学员在微信群里用的：<strong>收到、加油、辛苦了</strong>，
  还有几个只有学过急救的人才用得上的——<strong>快打911、用力按压、别慌</strong>。</p>

  <div class="callout">
    <h3>为什么不能一键添加整套？</h3>
    <p>微信只允许从它自己的表情商店一键添加整套表情，网页和文件都不行。要做到那一步，
    这套表情得先投稿到微信表情开放平台并通过审核。在那之前，用下面的办法自己加，
    一张十几秒，全部加完两分钟。</p>
  </div>

  <div class="grab">
    <a class="btn" href="allcpr-anan-stickers.zip" download>下载全部 16 枚（{zip_kb} KB）</a>
    <p>压缩包里含 16 个 GIF、16 张缩略图和详情页横幅。</p>
  </div>

  <h2>怎么加到自己的表情栏</h2>
  <p class="note">先把图片存下来，再从聊天里添加。</p>

  <div class="tracks">
    <div class="track">
      <h3>手机</h3>
      <ol>
        <li><span>长按下面任意一张表情，选<kbd>保存图片</kbd>（iPhone 是<kbd>存储到相册</kbd>）</span></li>
        <li><span>打开微信，把图片发到<kbd>文件传输助手</kbd>，发给自己就行<br>
        <em>英文版微信里它叫 <kbd>File Transfer</kbd>，在聊天列表里，绿色图标</em></span></li>
        <li><span>长按刚发出去的那张，点<kbd>添加到表情</kbd>，收工</span></li>
      </ol>
    </div>
    <div class="track">
      <h3>电脑</h3>
      <ol>
        <li><span>点上面的下载按钮，解压出 16 个 GIF</span></li>
        <li><span>在微信里把 GIF 发到<kbd>文件传输助手</kbd><br>
        <em>英文版微信里它叫 <kbd>File Transfer</kbd>，在聊天列表里，绿色图标</em></span></li>
        <li><span>右键点这张表情，选<kbd>添加到表情</kbd></span></li>
      </ol>
    </div>
  </div>

  <div class="share">
    <img src="assets/qr.png" alt="扫码打开本页" width="118" height="118">
    <div>
      <h3>发到群里</h3>
      <p>扫这个码，或者直接把下面这条链接发到微信群，同事自己就能下。</p>
      <code>{SITE_URL}</code>
    </div>
  </div>

  <h2>全部 16 枚</h2>
  <p class="note">每张都在动。长按图片可直接保存。</p>
  <div class="grid">
{tiles}
  </div>

  <footer>
    <p>素材按微信表情开放平台的规范做：主图 240×240 GIF、每张不超过 100KB；
    缩略图 240×240 PNG、不超过 60KB；一套 16 枚。以后要正式上架表情商店，素材是齐的。</p>
    <p><a href="https://allcpr.org">allcpr.org</a> · 人人都应学 CPR</p>
  </footer>
</div>
</body>
</html>
"""

(SITE / "index.html").write_text(HTML)

(ROOT / "render.yaml").write_text("""# Render Blueprint - static hosting for the ALLCPR sticker download page.
# Docs: https://render.com/docs/blueprint-spec
services:
  - type: web
    name: allcpr-stickers
    runtime: static
    buildCommand: "echo 'static site - no build step'"
    staticPublishPath: ./site
    headers:
      - path: /*
        name: X-Content-Type-Options
        value: nosniff
      - path: /stickers/*
        name: Cache-Control
        value: public, max-age=604800
""")

total = sum(f.stat().st_size for f in SITE.rglob("*") if f.is_file())
print(f"site built: {SITE}")
print(f"  files {sum(1 for f in SITE.rglob('*') if f.is_file())}, total {total/1024/1024:.2f} MB")
print(f"  zip {zip_kb} KB")
