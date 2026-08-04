#!/usr/bin/env python3
"""Generate the self-contained download page: 16 GIFs + the zip, all inlined."""

import base64
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).parent
DELIV = ROOT / "06_deliverable"
GIFDIR = DELIV / "01_主图_main_gif"
ZIP = DELIV / "ALLCPR_安安_微信表情包_16枚.zip"
OUT = DELIV / "download-page.html"


def b64(p):
    return base64.b64encode(p.read_bytes()).decode()


def logo_b64():
    im = Image.open(ROOT / "00_ref" / "allcpr_logo_full.png").convert("RGB")
    im.thumbnail((160, 160), Image.LANCZOS)
    tmp = ROOT / "00_ref" / "_logo_small.png"
    im.save(tmp, optimize=True)
    return b64(tmp)


spec = json.loads((ROOT / "captions.json").read_text())
stickers = spec["stickers"]

tiles = []
for s in stickers:
    sid, cap = s["id"], s["caption"]
    data = b64(GIFDIR / f"{sid}.gif")
    tiles.append(f"""      <figure class="tile">
        <div class="art"><img src="data:image/gif;base64,{data}" alt="{cap}" loading="lazy"></div>
        <figcaption>
          <span class="cap">{cap}</span>
          <a class="save" download="ALLCPR_{sid}_{cap}.gif">保存</a>
        </figcaption>
      </figure>""")

zip_kb = round(ZIP.stat().st_size / 1024)

HTML = f"""<title>ALLCPR 安安 · 微信表情包</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root {{
    --blue:#00A0E9; --blue-ink:#0076AE; --wash:#EAF6FE; --red:#E30613;
    --paper:#EEF5FA; --ink:#0F2230; --muted:#4A6675; --line:#D6E4EE;
    --tile:#FFFFFF; --shadow:0 1px 2px rgba(15,34,48,.06), 0 8px 20px rgba(15,34,48,.06);
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --blue:#3FBDF7; --blue-ink:#8AD6FB; --wash:#132735; --red:#FF5A63;
      --paper:#0B1621; --ink:#E9F2F8; --muted:#94AFC1; --line:#1D3243;
      --tile:#FFFFFF; --shadow:0 1px 2px rgba(0,0,0,.4), 0 10px 26px rgba(0,0,0,.34);
    }}
  }}
  :root[data-theme="light"] {{
    --blue:#00A0E9; --blue-ink:#0076AE; --wash:#EAF6FE; --red:#E30613;
    --paper:#EEF5FA; --ink:#0F2230; --muted:#4A6675; --line:#D6E4EE;
    --tile:#FFFFFF; --shadow:0 1px 2px rgba(15,34,48,.06), 0 8px 20px rgba(15,34,48,.06);
  }}
  :root[data-theme="dark"] {{
    --blue:#3FBDF7; --blue-ink:#8AD6FB; --wash:#132735; --red:#FF5A63;
    --paper:#0B1621; --ink:#E9F2F8; --muted:#94AFC1; --line:#1D3243;
    --tile:#FFFFFF; --shadow:0 1px 2px rgba(0,0,0,.4), 0 10px 26px rgba(0,0,0,.34);
  }}

  * {{ box-sizing:border-box; }}
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
    display:grid; place-items:center; box-shadow:var(--shadow); overflow:hidden;
  }}
  .hero img {{ width:100%; height:100%; object-fit:contain; }}
  .titles {{ flex:1 1 240px; min-width:0; }}
  h1 {{
    margin:0; font-size:clamp(28px,5vw,40px); font-weight:900;
    letter-spacing:-.02em; text-wrap:balance;
  }}
  h1 .en {{ color:var(--blue); }}
  .sub {{ margin:6px 0 0; color:var(--muted); font-size:15px; }}
  .brandmark {{ width:44px; height:44px; border-radius:50%; flex:none; opacity:.9; }}

  .lede {{ margin:26px 0 0; max-width:62ch; color:var(--muted); }}
  .lede strong {{ color:var(--ink); font-weight:600; }}

  .grab {{
    margin:26px 0 0; display:flex; align-items:center; gap:16px; flex-wrap:wrap;
    padding:18px 20px; background:var(--wash); border:1px solid var(--line);
    border-radius:14px;
  }}
  .btn {{
    display:inline-block; background:var(--blue); color:#fff; font-weight:700;
    text-decoration:none; padding:12px 22px; border-radius:10px; font-size:16px;
    transition:transform .15s ease, filter .15s ease;
  }}
  .btn:hover {{ filter:brightness(1.06); transform:translateY(-1px); }}
  .btn:focus-visible, .save:focus-visible {{ outline:3px solid var(--blue-ink); outline-offset:3px; }}
  .grab p {{ margin:0; font-size:14px; color:var(--muted); }}

  h2 {{
    margin:52px 0 0; font-size:13px; font-weight:700; letter-spacing:.14em;
    text-transform:uppercase; color:var(--blue-ink);
  }}
  h2 + .note {{ margin-top:8px; color:var(--muted); font-size:14px; }}

  .tracks {{ display:grid; gap:20px; grid-template-columns:1fr 1fr; margin-top:20px; }}
  @media (max-width:660px) {{ .tracks {{ grid-template-columns:1fr; }} }}
  .track {{
    background:var(--wash); border:1px solid var(--line); border-radius:14px; padding:22px 24px;
  }}
  .track h3 {{ margin:0 0 14px; font-size:17px; font-weight:800; }}
  ol {{ margin:0; padding:0; list-style:none; counter-reset:step; display:grid; gap:12px; }}
  ol li {{ counter-increment:step; display:grid; grid-template-columns:26px 1fr; gap:12px; }}
  ol li::before {{
    content:counter(step); grid-row:span 2; width:26px; height:26px; border-radius:50%;
    background:var(--blue); color:#fff; font-size:13px; font-weight:800;
    display:grid; place-items:center; font-variant-numeric:tabular-nums;
  }}
  ol li span {{ align-self:center; }}
  kbd {{
    font:inherit; font-weight:700; background:var(--tile); color:#0F2230;
    border:1px solid var(--line); border-radius:6px; padding:1px 7px; white-space:nowrap;
  }}

  .grid {{
    margin-top:20px; display:grid; gap:16px;
    grid-template-columns:repeat(4,1fr);
  }}
  @media (max-width:860px) {{ .grid {{ grid-template-columns:repeat(3,1fr); }} }}
  @media (max-width:600px) {{ .grid {{ grid-template-columns:repeat(2,1fr); }} }}
  .tile {{ margin:0; border-radius:14px; overflow:hidden; box-shadow:var(--shadow); background:var(--tile); }}
  .art {{ background:#fff; }}
  .art img {{ display:block; width:100%; height:auto; }}
  figcaption {{
    display:flex; align-items:center; justify-content:space-between; gap:8px;
    padding:10px 12px; background:var(--tile); border-top:1px solid #E8EEF3;
  }}
  .cap {{ font-weight:700; font-size:15px; color:#0F2230; }}
  .save {{
    font-size:13px; font-weight:700; color:var(--blue-ink); text-decoration:none;
    border:1px solid var(--line); border-radius:7px; padding:3px 10px; background:#fff;
  }}
  .save:hover {{ background:var(--wash); }}

  footer {{
    margin-top:56px; padding-top:24px; border-top:1px solid var(--line);
    color:var(--muted); font-size:14px;
  }}
  footer p {{ margin:0 0 8px; max-width:66ch; }}
  .heart {{ color:var(--red); }}

  @media (prefers-reduced-motion: reduce) {{
    * {{ transition:none !important; }}
  }}
</style>

<div class="wrap">
  <header>
    <div class="hero"><img src="data:image/gif;base64,{b64(GIFDIR / '12.gif')}" alt="安安"></div>
    <div class="titles">
      <h1><span class="en">ALLCPR</span> 安安</h1>
      <p class="sub">微信表情包 · 16 枚 · 会动的 GIF</p>
    </div>
    <img class="brandmark" src="data:image/png;base64,{logo_b64()}" alt="ALLCPR">
  </header>

  <p class="lede">安安戴的是 ALLCPR 的标志——蓝色的 A 里面一颗<span class="heart">红心</span>。
  这套表情是给 ALLCPR 的同事和学员在微信群里用的：<strong>收到、加油、辛苦了</strong>，
  还有几个只有学过急救的人才用得上的——<strong>快打911、用力按压、别慌</strong>。</p>

  <div class="grab">
    <a class="btn" id="zip" download="ALLCPR_安安_微信表情包.zip">下载全部 16 枚</a>
    <p>ZIP 压缩包，约 {zip_kb} KB。也可以在下面单张保存。</p>
  </div>

  <h2>怎么加到自己的表情栏</h2>
  <p class="note">微信不能直接从网页装表情包，得先把图片存下来，再从聊天里添加。两分钟的事。</p>

  <div class="tracks">
    <div class="track">
      <h3>手机</h3>
      <ol>
        <li><span>长按下面任意一张表情，选<kbd>保存图片</kbd>（iPhone 是<kbd>存储到相册</kbd>）</span></li>
        <li><span>打开微信，把图片发到<kbd>文件传输助手</kbd>，发给自己就行</span></li>
        <li><span>长按刚发出去的那张，点<kbd>添加到表情</kbd>，收工</span></li>
      </ol>
    </div>
    <div class="track">
      <h3>电脑</h3>
      <ol>
        <li><span>点上面的<kbd>下载全部 16 枚</kbd>，解压出 16 个 GIF</span></li>
        <li><span>在微信里把 GIF 发到<kbd>文件传输助手</kbd></span></li>
        <li><span>右键点这张表情，选<kbd>添加到表情</kbd></span></li>
      </ol>
    </div>
  </div>

  <h2>全部 16 枚</h2>
  <p class="note">每张都在动。长按图片可直接保存。</p>
  <div class="grid">
{chr(10).join(tiles)}
  </div>

  <footer>
    <p>尺寸按微信表情开放平台的规范做的：主图 240×240 GIF、每张不超过 100KB，
    缩略图 240×240 PNG、不超过 60KB，一套 16 枚。上面的下载包里已经含缩略图和详情页横幅，
    如果以后要正式上架微信表情商店，素材是齐的。</p>
    <p>allcpr.org · 人人都应学 CPR</p>
  </footer>
</div>

<script>
  document.getElementById('zip').href =
    'data:application/zip;base64,{b64(ZIP)}';
  document.querySelectorAll('.tile').forEach(function (t) {{
    t.querySelector('.save').href = t.querySelector('img').src;
  }});
</script>
"""

OUT.write_text(HTML)
print(f"wrote {OUT}  ({OUT.stat().st_size/1024/1024:.2f} MB)")
