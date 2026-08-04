#!/usr/bin/env python3
"""Build the public static site served from Render.

Two full sticker sets, Chinese and English, from the same animations. The page
toggles between them; each view stays in one language throughout.

Unlike the self-contained artifact page, this references real .gif files:
long-press-to-save is more reliable against a real URL than a data URI, and the
page loads progressively instead of shipping everything up front.
"""

import json
import shutil
import zipfile
from pathlib import Path

import segno
from PIL import Image

ROOT = Path(__file__).parent
DELIV = ROOT / "06_deliverable"
SITE = ROOT / "site"
SITE_URL = "https://allcpr-stickers.onrender.com"

LANGS = {
    "zh": {"main": DELIV / "zh" / "01_主图_main_gif",
           "thumb": DELIV / "zh" / "02_缩略图_thumbnail_png", "key": "caption"},
    "en": {"main": DELIV / "en" / "01_main_gif",
           "thumb": DELIV / "en" / "02_thumbnail_png", "key": "caption_en"},
}

spec = json.loads((ROOT / "captions.json").read_text())
stickers = spec["stickers"]

# ---------------------------------------------------------------- files
if SITE.exists():
    shutil.rmtree(SITE)
(SITE / "assets").mkdir(parents=True)

zip_kb = {}
for lang, cfg in LANGS.items():
    (SITE / "stickers" / lang).mkdir(parents=True)
    for s in stickers:
        shutil.copy(cfg["main"] / f"{s['id']}.gif", SITE / "stickers" / lang / f"{s['id']}.gif")

    zp = SITE / f"allcpr-anan-stickers-{lang}.zip"
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for s in stickers:
            sid, cap = s["id"], s[cfg["key"]]
            safe = cap.replace("/", "-")
            z.write(cfg["main"] / f"{sid}.gif", f"main/{sid}_{safe}.gif")
            z.write(cfg["thumb"] / f"{sid}.png", f"thumbnail/{sid}_{safe}.png")
        z.write(DELIV / lang / f"03_banner_750x400_{lang}.png", f"banner_750x400_{lang}.png")
    zip_kb[lang] = round(zp.stat().st_size / 1024)

logo = Image.open(ROOT / "00_ref" / "allcpr_logo_full.png").convert("RGB")
logo.thumbnail((160, 160), Image.LANCZOS)
logo.save(SITE / "assets" / "allcpr-logo.png", optimize=True)
shutil.copy(DELIV / "zh" / "04_preview_zh.png", SITE / "assets" / "preview.png")

segno.make(SITE_URL, error="h").save(
    SITE / "assets" / "qr.png", scale=9, border=2, dark="#0F2230", light="#FFFFFF")


def grid(lang):
    cfg = LANGS[lang]
    tiles = "\n".join(
        f"""      <figure class="tile">
        <div class="art"><img src="stickers/{lang}/{s['id']}.gif" alt="{s[cfg['key']]}" width="240" height="240" loading="lazy"></div>
        <figcaption>
          <span class="cap">{s[cfg['key']]}</span>
          <a class="save" href="stickers/{lang}/{s['id']}.gif" download="ALLCPR_{s['id']}.gif">{'保存' if lang == 'zh' else 'Save'}</a>
        </figcaption>
      </figure>"""
        for s in stickers)
    return f'  <div class="grid" lang="{lang}">\n{tiles}\n  </div>'


HTML = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>ALLCPR 安安 · 微信表情包 | WeChat Sticker Pack</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="ALLCPR 安安 微信表情包，24 枚会动的 GIF，中英双版，免费下载。ALLCPR An An WeChat sticker pack: 24 animated stickers in Chinese and English.">
<meta property="og:title" content="ALLCPR 安安 · 微信表情包">
<meta property="og:description" content="24 枚会动的 GIF，中英双版。收到、加油、辛苦了，还有快打911、用力按压。">
<meta property="og:image" content="assets/preview.png">
<link rel="icon" href="assets/allcpr-logo.png">
<style>
  :root {{
    --blue:#00A0E9; --blue-ink:#0076AE; --wash:#EAF6FE; --red:#E30613;
    --paper:#EEF5FA; --ink:#0F2230; --muted:#4A6675; --line:#D6E4EE;
    --chat:#EDEDED;
    --shadow:0 1px 2px rgba(15,34,48,.06), 0 8px 20px rgba(15,34,48,.06);
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --blue:#3FBDF7; --blue-ink:#8AD6FB; --wash:#132735; --red:#FF5A63;
      --paper:#0B1621; --ink:#E9F2F8; --muted:#94AFC1; --line:#1D3243;
      --chat:#243542;
      --shadow:0 1px 2px rgba(0,0,0,.4), 0 10px 26px rgba(0,0,0,.34);
    }}
  }}
  :root[data-theme="light"] {{
    --blue:#00A0E9; --blue-ink:#0076AE; --wash:#EAF6FE; --red:#E30613;
    --paper:#EEF5FA; --ink:#0F2230; --muted:#4A6675; --line:#D6E4EE; --chat:#EDEDED;
    --shadow:0 1px 2px rgba(15,34,48,.06), 0 8px 20px rgba(15,34,48,.06);
  }}
  :root[data-theme="dark"] {{
    --blue:#3FBDF7; --blue-ink:#8AD6FB; --wash:#132735; --red:#FF5A63;
    --paper:#0B1621; --ink:#E9F2F8; --muted:#94AFC1; --line:#1D3243; --chat:#243542;
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
  .wrap {{ max-width:1000px; margin:0 auto; padding:0 20px 72px; }}

  /* one language at a time - each view stays internally consistent */
  body[data-lang="zh"] [lang="en"] {{ display:none; }}
  body[data-lang="en"] [lang="zh"] {{ display:none; }}

  header {{
    display:flex; align-items:center; gap:20px; flex-wrap:wrap;
    padding:32px 0 26px; border-bottom:1px solid var(--line);
  }}
  .hero {{
    width:104px; height:104px; flex:none; border-radius:20px; background:var(--chat);
    box-shadow:var(--shadow); overflow:hidden;
  }}
  .hero img {{ display:block; width:100%; height:100%; object-fit:contain; }}
  .titles {{ flex:1 1 240px; min-width:0; }}
  h1 {{ margin:0; font-size:clamp(26px,5vw,38px); font-weight:900; letter-spacing:-.02em; text-wrap:balance; }}
  h1 .en {{ color:var(--blue); }}
  .sub {{ margin:6px 0 0; color:var(--muted); font-size:15px; }}

  .langtog {{ display:flex; gap:0; border:1px solid var(--line); border-radius:10px; overflow:hidden; flex:none; }}
  .langtog button {{
    font:inherit; font-size:14px; font-weight:700; padding:8px 16px; cursor:pointer;
    border:0; background:transparent; color:var(--muted);
  }}
  .langtog button[aria-pressed="true"] {{ background:var(--blue); color:#fff; }}
  .langtog button:focus-visible {{ outline:3px solid var(--blue-ink); outline-offset:-3px; }}

  .lede {{ margin:24px 0 0; max-width:62ch; color:var(--muted); }}
  .lede strong {{ color:var(--ink); font-weight:600; }}
  .heart {{ color:var(--red); }}

  .callout {{
    margin:24px 0 0; padding:18px 22px; border-radius:14px;
    background:var(--wash); border:1px solid var(--line); border-left:4px solid var(--blue);
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

  h2 {{ margin:48px 0 0; font-size:13px; font-weight:700; letter-spacing:.14em; text-transform:uppercase; color:var(--blue-ink); }}
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
    margin-top:26px; display:flex; align-items:center; gap:22px; flex-wrap:wrap;
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

  .grid {{ margin-top:20px; display:grid; gap:14px; grid-template-columns:repeat(6,1fr); }}
  @media (max-width:900px) {{ .grid {{ grid-template-columns:repeat(4,1fr); }} }}
  @media (max-width:620px) {{ .grid {{ grid-template-columns:repeat(3,1fr); }} }}
  @media (max-width:420px) {{ .grid {{ grid-template-columns:repeat(2,1fr); }} }}
  .tile {{ margin:0; border-radius:14px; overflow:hidden; box-shadow:var(--shadow); background:var(--chat); }}
  /* chat grey behind each sticker, because the GIFs are transparent */
  .art {{ background:var(--chat); }}
  .art img {{ display:block; width:100%; height:auto; }}
  figcaption {{
    display:flex; align-items:center; justify-content:space-between; gap:6px;
    padding:8px 10px; background:#fff; border-top:1px solid #E8EEF3;
  }}
  .cap {{ font-weight:700; font-size:13.5px; color:#0F2230; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
  .save {{
    font-size:12px; font-weight:700; color:#0076AE; text-decoration:none;
    border:1px solid #D6E4EE; border-radius:7px; padding:2px 8px; background:#fff; flex:none;
  }}
  .save:hover {{ background:#EAF6FE; }}

  footer {{ margin-top:52px; padding-top:24px; border-top:1px solid var(--line); color:var(--muted); font-size:14px; }}
  footer p {{ margin:0 0 8px; max-width:66ch; }}
  footer a {{ color:var(--blue-ink); }}

  @media (prefers-reduced-motion: reduce) {{ * {{ transition:none !important; }} }}
</style>
</head>
<body data-lang="zh">
<div class="wrap">
  <header>
    <div class="hero"><img src="stickers/zh/12.gif" alt="安安 / An An" width="240" height="240"></div>
    <div class="titles">
      <h1><span class="en">ALLCPR</span> <span lang="zh">安安</span><span lang="en">An An</span></h1>
      <p class="sub" lang="zh">微信表情包 · 24 枚 · 会动的 GIF · 中英双版</p>
      <p class="sub" lang="en">WeChat sticker pack · 24 animated stickers · Chinese and English</p>
    </div>
    <div class="langtog" role="group" aria-label="Language">
      <button type="button" data-set="zh" aria-pressed="true">中文</button>
      <button type="button" data-set="en" aria-pressed="false">English</button>
    </div>
  </header>

  <p class="lede" lang="zh">安安戴的是 ALLCPR 的标志——蓝色的 A 里面一颗<span class="heart">红心</span>。
  这套表情是给 ALLCPR 的同事和学员在微信群里用的：<strong>收到、加油、辛苦了</strong>，
  还有几个只有学过急救的人才用得上的——<strong>快打911、用力按压、别慌</strong>。</p>
  <p class="lede" lang="en">An An wears the ALLCPR mark as a hood: the blue "A" with a
  <span class="heart">red heart</span> inside it. The pack is for ALLCPR staff and students
  in group chats: <strong>Got it, You got this, Great work</strong> — plus a few only people
  who have taken the class will use: <strong>Call 911, Push hard, Stay calm</strong>.</p>

  <div class="callout">
    <h3 lang="zh">为什么不能一键添加整套？</h3>
    <h3 lang="en">Why isn't there a one-tap "add all"?</h3>
    <p lang="zh">微信只允许从它自己的表情商店一键添加整套表情，网页和文件都不行。要做到那一步，
    这套表情得先投稿到微信表情开放平台并通过审核。在那之前，用下面的办法自己加，
    一张十几秒，全部加完两三分钟。</p>
    <p lang="en">WeChat only allows one-tap install for packs published in its own sticker
    store — there is no import format for a web page or a file. Getting there means
    submitting this pack to the WeChat Sticker Open Platform and passing review. Until then,
    add them yourself with the steps below: about ten seconds each.</p>
  </div>

  <div class="grab">
    <a class="btn" lang="zh" href="allcpr-anan-stickers-zh.zip" download>下载全部 24 枚（{zip_kb['zh']} KB）</a>
    <a class="btn" lang="en" href="allcpr-anan-stickers-en.zip" download>Download all 24 ({zip_kb['en']} KB)</a>
    <p lang="zh">压缩包里含 24 个 GIF、24 张缩略图和详情页横幅。</p>
    <p lang="en">The zip holds 24 GIFs, 24 thumbnails and the detail-page banner.</p>
  </div>

  <h2 lang="zh">怎么加到自己的表情栏</h2>
  <h2 lang="en">Adding them to your stickers</h2>
  <p class="note" lang="zh">先把图片存下来，再从聊天里添加。</p>
  <p class="note" lang="en">Save the image first, then add it from a chat.</p>

  <div class="tracks">
    <div class="track">
      <h3 lang="zh">手机</h3>
      <h3 lang="en">Phone</h3>
      <ol lang="zh">
        <li><span>长按下面任意一张表情，选<kbd>保存图片</kbd>（iPhone 是<kbd>存储到相册</kbd>）</span></li>
        <li><span>打开微信，把图片发到<kbd>文件传输助手</kbd>，发给自己就行<br>
        <em>英文版微信里它叫 <kbd>File Transfer</kbd>，在聊天列表里，绿色图标</em></span></li>
        <li><span>长按刚发出去的那张，点<kbd>添加到表情</kbd>，收工</span></li>
      </ol>
      <ol lang="en">
        <li><span>Long-press any sticker below and choose <kbd>Save Image</kbd></span></li>
        <li><span>In WeChat, send it to <kbd>File Transfer</kbd> — a chat with yourself<br>
        <em>Called <kbd>文件传输助手</kbd> in the Chinese app. Green icon in your chat list.</em></span></li>
        <li><span>Long-press the sticker you just sent and tap <kbd>Add to Stickers</kbd></span></li>
      </ol>
    </div>
    <div class="track">
      <h3 lang="zh">电脑</h3>
      <h3 lang="en">Computer</h3>
      <ol lang="zh">
        <li><span>点上面的下载按钮，解压出 24 个 GIF</span></li>
        <li><span>把 GIF 直接拖进<kbd>文件传输助手</kbd>的聊天窗口<br>
        <em>英文版微信里它叫 <kbd>File Transfer</kbd></em></span></li>
        <li><span>右键点这张表情，选<kbd>添加到表情</kbd></span></li>
      </ol>
      <ol lang="en">
        <li><span>Use the download button above and unzip the 24 GIFs</span></li>
        <li><span>Drag a GIF straight into the <kbd>File Transfer</kbd> chat window</span></li>
        <li><span>Right-click the sticker and choose <kbd>Add to Stickers</kbd></span></li>
      </ol>
    </div>
  </div>

  <div class="share">
    <img src="assets/qr.png" alt="QR" width="118" height="118">
    <div>
      <h3 lang="zh">发到群里</h3>
      <h3 lang="en">Share it</h3>
      <p lang="zh">扫这个码，或者直接把下面这条链接发到微信群，同事自己就能下。</p>
      <p lang="en">Scan this, or paste the link below into a group chat.</p>
      <code>{SITE_URL}</code>
    </div>
  </div>

  <h2 lang="zh">全部 24 枚</h2>
  <h2 lang="en">All 24 stickers</h2>
  <p class="note" lang="zh">每张都在动，背景是透明的。长按图片可直接保存。</p>
  <p class="note" lang="en">All animated, all transparent. Long-press to save.</p>
{grid('zh')}
{grid('en')}

  <footer>
    <p lang="zh">素材按微信表情开放平台的规范做：主图 240×240 GIF、每张不超过 100KB、背景透明；
    缩略图 240×240 PNG、不超过 60KB；一套 24 枚。以后要正式上架表情商店，素材是齐的。</p>
    <p lang="en">Built to the WeChat Sticker Open Platform spec: 240×240 GIF under 100KB each
    with a transparent background, 240×240 PNG thumbnails under 60KB, 24 to a set. Everything
    needed for a store submission is here.</p>
    <p><a href="https://allcpr.org">allcpr.org</a> · <span lang="zh">人人都应学 CPR</span><span lang="en">All of us should learn CPR</span></p>
  </footer>
</div>

<script>
  (function () {{
    var body = document.body;
    var saved = null;
    try {{ saved = localStorage.getItem('allcpr-lang'); }} catch (e) {{}}
    if (!saved) {{
      saved = (navigator.language || '').toLowerCase().indexOf('zh') === 0 ? 'zh' : 'en';
    }}
    function set(lang) {{
      body.setAttribute('data-lang', lang);
      document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en';
      document.querySelectorAll('.langtog button').forEach(function (b) {{
        b.setAttribute('aria-pressed', String(b.dataset.set === lang));
      }});
      try {{ localStorage.setItem('allcpr-lang', lang); }} catch (e) {{}}
    }}
    document.querySelectorAll('.langtog button').forEach(function (b) {{
      b.addEventListener('click', function () {{ set(b.dataset.set); }});
    }});
    set(saved);
  }})();
</script>
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

files = [f for f in SITE.rglob("*") if f.is_file()]
print(f"site built: {SITE}")
print(f"  files {len(files)}, total {sum(f.stat().st_size for f in files)/1024/1024:.2f} MB")
print(f"  zips: zh {zip_kb['zh']} KB, en {zip_kb['en']} KB")
