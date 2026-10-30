#!/usr/bin/env python3
"""Lấy số liệu thật và vẽ projects.svg (2 thẻ kính, khung đầu tiên đầy đủ, vòng 8s)."""
import base64, json, pathlib, sys, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
OUTS = [ROOT / "projects-ext.svg", ROOT / "projects-app.svg"]  # mỗi thẻ 1 ảnh, để gắn link riêng

# ---- Cấu hình: sửa mô tả / link ở đây (chỉ dùng ký tự ASCII và "·" để khớp font nhúng) ----
EXT_ID = "nhatnam7kz.c-auto-template"
REPO = "nhatnam7kz/TrueClose"
CARDS = [
    dict(eyebrow="VS CODE EXTENSION", title="C/C++ Auto Template",
         desc="Inserts a C/C++ template into empty .c/.cpp files.",
         label="installs", cta="VIEW ON MARKETPLACE", accent="#60a5fa",
         url=f"https://marketplace.visualstudio.com/items?itemName={EXT_ID}", icon="ext"),
    dict(eyebrow="MACOS APP", title="TrueClose",
         desc="Menu bar app that auto-quits apps with no windows.",
         label="downloads", cta="VIEW ON GITHUB", accent="#5eead4",
         url=f"https://github.com/{REPO}", icon="apple"),
]
APPLE = open(ROOT / "apple.txt").read().strip() if (ROOT / "apple.txt").exists() else ""
EXT_PATH = ("M20.5 11H19V7c0-1.1-.9-2-2-2h-4V3.5C13 2.12 11.88 1 10.5 1S8 2.12 8 3.5V5H4c-1.1 0-1.99.9-1.99 2v3.8H3.5"
            "c1.49 0 2.7 1.21 2.7 2.7s-1.21 2.7-2.7 2.7H2V20c0 1.1.9 2 2 2h3.8v-1.5c0-1.49 1.21-2.7 2.7-2.7 1.49 0 2.7 1.21 2.7 2.7"
            "V22H17c1.1 0 2-.9 2-2v-4h1.5c1.38 0 2.5-1.12 2.5-2.5S21.88 11 20.5 11z")


ADV = {'0': .675, '1': .561, '2': .548, '3': .591, '4': .662, '5': .596, '6': .579, '7': .553, '8': .599, '9': .577, ',': .287}
COUNT_START, COUNT_DUR, FRAMES = 0.05, 1.8, 36   # đếm một lần khi ảnh vừa tải

def text_w(t, size=30):
    return sum(ADV[ch] for ch in t) * size

def counter(x, y, final, label_class_x):
    """Số đếm 0 -> final bằng SMIL. Giá trị cuối luôn là phần tử gốc (hiện sẵn ở t=0),
    nên trình xem chỉ vẽ khung đầu vẫn thấy số thật."""
    step = COUNT_DUR / FRAMES
    vals = []
    for k in range(FRAMES):
        t = (k + 1) / FRAMES
        vals.append(final if k == FRAMES - 1 else round(final * (1 - (1 - t) ** 3)))
    out = [f'<text x="{x}" y="{y}" class="nu" fill="url(#num)">{final:,}'
           f'<set attributeName="visibility" to="hidden" begin="{COUNT_START}s" dur="{COUNT_DUR:.2f}s"/></text>']
    prev = None
    for k, v in enumerate(vals):
        if v == prev:
            continue
        prev = v
        out.append(f'<text x="{x}" y="{y}" class="nu" fill="url(#num)" visibility="hidden">{v:,}'
                   f'<set attributeName="visibility" to="visible" begin="{COUNT_START + k*step:.3f}s" dur="{step:.3f}s"/></text>')
    out.append(f'<text x="{label_class_x:.1f}" y="{y}" class="lb">LABEL</text>')
    return "".join(out)

def get(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    return json.load(urllib.request.urlopen(req, timeout=30))

def ext_installs():
    body = json.dumps({"filters": [{"criteria": [{"filterType": 7, "value": EXT_ID}]}], "flags": 914}).encode()
    r = get("https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery", body,
            {"Content-Type": "application/json", "Accept": "application/json;api-version=3.0-preview.1"})
    stats = r["results"][0]["extensions"][0]["statistics"]
    return int(next(s["value"] for s in stats if s["statisticName"] == "install"))

def repo_downloads():
    rels = get(f"https://api.github.com/repos/{REPO}/releases?per_page=100", headers={"User-Agent": "stats"})
    return sum(a["download_count"] for r in rels for a in r["assets"])

def font(name, family, weight):
    b = base64.b64encode((ROOT / name).read_bytes()).decode()
    return (f"@font-face{{font-family:'{family}';font-weight:{weight};"
            f"src:url(data:font/woff2;base64,{b}) format('woff2');}}")

ADV = {"0": .675, "1": .561, "2": .548, "3": .591, "4": .662, "5": .596, "6": .579, "7": .553, "8": .599, "9": .577, ",": .287}
COUNT_SECS, COUNT_FPS = 2.2, 24  # đếm từ 0 lên giá trị thật, chạy 1 lần khi mở trang

def num_width(txt, size=30):
    return sum(ADV.get(ch, .6) for ch in txt) * size

def counter(value, x, y, gap=8):
    """SMIL không đổi được nội dung chữ, nên vẽ sẵn từng khung số và bật/tắt bằng <set>."""
    n = int(COUNT_SECS * COUNT_FPS)
    seq = [round(value * (1 - (1 - k / n) ** 3)) for k in range(n)]  # ease-out
    out, k, kt, xs = [], 0, [], []
    while k < n:
        j = k
        while j + 1 < n and seq[j + 1] == seq[k]:
            j += 1
        st, du = k / COUNT_FPS, (j - k + 1) / COUNT_FPS
        out.append(f'<text x="{x}" y="{y}" class="nu" fill="url(#num)" visibility="hidden">{seq[k]:,}'
                   f'<set attributeName="visibility" to="visible" begin="{st:.3f}s" dur="{du:.3f}s"/></text>')
        kt.append(st / COUNT_SECS); xs.append(x + num_width(f"{seq[k]:,}") + gap)
        k = j + 1
    # số cuối: là bản hiển thị mặc định (trình xem không chạy SMIL vẫn thấy đúng số), chỉ ẩn trong lúc đếm
    out.append(f'<text x="{x}" y="{y}" class="nu" fill="url(#num)">{value:,}'
               f'<set attributeName="visibility" to="hidden" begin="0s" dur="{COUNT_SECS}s"/></text>')
    kt.append(1.0); xs.append(x + num_width(f"{value:,}") + gap)
    anim = (f'<animate attributeName="x" calcMode="discrete" dur="{COUNT_SECS}s" fill="freeze" '
            f'keyTimes="{";".join(f"{t:.4f}" for t in kt)}" values="{";".join(f"{v:.1f}" for v in xs)}"/>')
    return "".join(out), anim

def card(i, c, value, ox, cta_w, oy=20, w=450, h=170):
    ic = EXT_PATH if c["icon"] == "ext" else APPLE
    cx, cy = ox + 50, oy + 50
    s = 22 / 24
    txt = f"{value:,}"
    ny = oy + 142
    cnt, lbl_anim = counter(value, ox + 26, ny)
    lx = ox + 26 + num_width(txt) + 8
    chip_x = ox + w - 26 - cta_w
    chip_y = oy + h - 26 - 28
    return f'''
<a href="{c["url"]}" target="_blank">
<g>
  <rect x="{ox}" y="{oy}" width="{w}" height="{h}" rx="26" fill="#0a1530" fill-opacity=".35"/>
  <rect x="{ox}" y="{oy}" width="{w}" height="{h}" rx="26" fill="url(#sheen)"/>
  <rect x="{ox+.5}" y="{oy+.5}" width="{w-1}" height="{h-1}" rx="25.5" fill="none" stroke="url(#edge)" stroke-width="1"/>
  <line x1="{ox+34}" y1="{oy+.8}" x2="{ox+w-34}" y2="{oy+.8}" stroke="#fff" stroke-opacity=".5" stroke-width="1.5" stroke-linecap="round"/>
  <rect x="{ox+.5}" y="{oy+.5}" width="{w-1}" height="{h-1}" rx="25.5" fill="none" stroke="url(#beam)" stroke-width="1.6"
        pathLength="1000" stroke-dasharray="90 910" stroke-linecap="round">
    <animate attributeName="stroke-dashoffset" values="0;-1000" dur="8s" repeatCount="indefinite"/>
  </rect>
  <circle cx="{cx}" cy="{cy}" r="24" fill="{c["accent"]}" fill-opacity=".13"/>
  <circle cx="{cx}" cy="{cy}" r="23.5" fill="none" stroke="{c["accent"]}" stroke-width="1">
    <animate attributeName="stroke-opacity" values=".35;.75;.35" dur="4s" repeatCount="indefinite"/>
  </circle>
  <path transform="translate({cx-11} {cy-11}) scale({s:.4f})" d="{ic}" fill="{c["accent"]}"/>
  <text x="{ox+96}" y="{oy+36}" class="eb">{c["eyebrow"]}</text>
  <text x="{ox+96}" y="{oy+62}" class="ti" fill="#fff">{c["title"]}</text>
  <text x="{ox+26}" y="{oy+96}" class="de">{c["desc"]}</text>
  {cnt}
  <text x="{lx:.1f}" y="{ny}" class="lb">{c["label"]}{lbl_anim}</text>
  <rect x="{chip_x}" y="{chip_y}" width="{cta_w:.1f}" height="28" rx="14" fill="#fff" fill-opacity=".08" stroke="#fff" stroke-opacity=".3"/>
  <text x="{chip_x+16:.1f}" y="{chip_y+18.5}" class="cta">{c["cta"]}</text>
  <path transform="translate({chip_x+cta_w-24:.1f} {chip_y+10})" d="M0 8L8 0M2 0H8V6" fill="none" stroke="#d6e4ff" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
</g></a>'''

def build(vals, idx):
    css = (font("lexend-700.woff2", "Lexend", 700) + font("inter-600.woff2", "Inter", 600) + font("inter-500.woff2", "Inter", 500) +
           ".eb{font:600 10.5px Inter,'Segoe UI',sans-serif;letter-spacing:1.5px;fill:#a5f3fc}"
           ".ti{font:700 22px Lexend,'Segoe UI',sans-serif;letter-spacing:-.2px}"
           ".de{font:500 13px Inter,'Segoe UI',sans-serif;fill:#9db4d8}"
           ".nu{font:700 30px Lexend,'Segoe UI',sans-serif}"
           ".lb{font:500 13px Inter,'Segoe UI',sans-serif;fill:#9db4d8}"
           ".cta{font:600 11px Inter,'Segoe UI',sans-serif;letter-spacing:1px;fill:#d6e4ff}")
    cta_w = max(len(c["cta"]) for c in CARDS) * 8.2 + 46  # 2 nút cùng độ rộng
    cards = card(idx, CARDS[idx], vals[idx], 25, cta_w)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="500" height="210" viewBox="0 0 500 210">
<defs>
<style>{css}</style>
<clipPath id="cv"><rect width="500" height="210" rx="20"/></clipPath>
<filter id="bl" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="60"/></filter>
<linearGradient id="sheen" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".13"/><stop offset="1" stop-color="#fff" stop-opacity=".03"/></linearGradient>
<linearGradient id="edge" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".45"/><stop offset=".5" stop-color="#fff" stop-opacity=".08"/><stop offset="1" stop-color="#22d3ee" stop-opacity=".35"/></linearGradient>
<linearGradient id="beam" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#22d3ee"/><stop offset="1" stop-color="#67e8f9"/></linearGradient>
<linearGradient id="num" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff"/><stop offset=".55" stop-color="#c7e0ff"/><stop offset="1" stop-color="#7ee8e0"/></linearGradient>
</defs>
<g clip-path="url(#cv)">
<rect width="500" height="210" fill="#050b1c"/>
<g filter="url(#bl)">
<circle r="110" fill="#2563eb" opacity=".5"><animate attributeName="cx" values="120;260;120" dur="8s" repeatCount="indefinite"/><animate attributeName="cy" values="50;150;50" dur="8s" repeatCount="indefinite"/></circle>
<circle r="100" fill="#14b8a6" opacity=".4"><animate attributeName="cx" values="400;280;400" dur="8s" repeatCount="indefinite"/><animate attributeName="cy" values="160;60;160" dur="8s" repeatCount="indefinite"/></circle>
</g>
</g>
<rect x=".5" y=".5" width="499" height="209" rx="19.5" fill="none" stroke="#fff" stroke-opacity=".1"/>
{cards}
</svg>'''

if __name__ == "__main__":
    try:
        vals = [ext_installs(), repo_downloads()]
    except Exception as e:
        print("LỖI - không lấy được số liệu, giữ nguyên file cũ:", repr(e), file=sys.stderr); sys.exit(1)
    for i, out in enumerate(OUTS):
        out.write_text(build(vals, i), encoding="utf-8")
    print("OK", vals)
