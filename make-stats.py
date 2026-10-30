#!/usr/bin/env python3
"""Vẽ github-stats.svg (thẻ kính) từ GitHub API, không phụ thuộc dịch vụ ngoài."""
import base64, json, os, pathlib, sys, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "github-stats.svg"
USER = "nhatnam7kz"
COLORS = ["#60a5fa", "#5eead4", "#a78bfa", "#fbbf24"]

def get(url):
    h = {"User-Agent": "stats", "Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        h["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=30))

def fetch():
    u = get(f"https://api.github.com/users/{USER}")
    repos = [r for r in get(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner") if not r["fork"]]
    langs = {}
    for r in repos:
        if r["language"]:
            langs[r["language"]] = langs.get(r["language"], 0) + 1
    tot = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda x: -x[1])[:4]
    return dict(repos=u["public_repos"], stars=sum(r["stargazers_count"] for r in repos),
                followers=u["followers"], langs=[(n, round(c * 100 / tot)) for n, c in top])

def font(name, family, weight):
    b = base64.b64encode((ROOT / name).read_bytes()).decode()
    return f"@font-face{{font-family:'{family}';font-weight:{weight};src:url(data:font/woff2;base64,{b}) format('woff2');}}"

def build(d):
    css = (font("lexend-700.woff2", "Lexend", 700) + font("inter-600.woff2", "Inter", 600) + font("inter-500.woff2", "Inter", 500) +
           ".eb{font:600 10.5px Inter,'Segoe UI',sans-serif;letter-spacing:1.5px;fill:#a5f3fc}"
           ".nu{font:700 30px Lexend,'Segoe UI',sans-serif}"
           ".lb{font:500 13px Inter,'Segoe UI',sans-serif;fill:#9db4d8}"
           ".lg{font:500 12.5px Inter,'Segoe UI',sans-serif;fill:#d6e4ff}")
    v = (lambda k: f"{d[k]:,}") if d else (lambda k: "-")
    stats = "".join(
        f'<text x="{x}" y="88" class="nu" fill="url(#num)">{v(k)}</text><text x="{x}" y="110" class="lb">{lab}</text>'
        for x, k, lab in ((84, "repos", "repositories"), (244, "stars", "stars earned"), (404, "followers", "followers")))
    langs = d["langs"] if d else []
    bar, leg, x0, W = "", "", 560, 340
    pos, lx = x0, x0
    for i, (n, p) in enumerate(langs):
        w = W * p / 100
        bar += f'<rect x="{pos:.1f}" y="70" width="{max(w - 3, 2):.1f}" height="8" rx="4" fill="{COLORS[i]}"/>'
        pos += w
        label = f"{n} {p}%"
        leg += f'<circle cx="{lx + 4:.1f}" cy="104" r="4" fill="{COLORS[i]}"/><text x="{lx + 14:.1f}" y="108" class="lg">{label}</text>'
        lx += 14 + len(label) * 6.9 + 16
    if not langs:
        bar = f'<rect x="{x0}" y="70" width="{W}" height="8" rx="4" fill="#fff" fill-opacity=".1"/>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="170" viewBox="0 0 1000 170">
<defs><style>{css}</style>
<clipPath id="cv"><rect width="1000" height="170" rx="20"/></clipPath>
<filter id="bl" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="60"/></filter>
<linearGradient id="sheen" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".13"/><stop offset="1" stop-color="#fff" stop-opacity=".03"/></linearGradient>
<linearGradient id="edge" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".45"/><stop offset=".5" stop-color="#fff" stop-opacity=".08"/><stop offset="1" stop-color="#22d3ee" stop-opacity=".35"/></linearGradient>
<linearGradient id="beam" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#22d3ee"/><stop offset="1" stop-color="#67e8f9"/></linearGradient>
<linearGradient id="num" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff"/><stop offset=".55" stop-color="#c7e0ff"/><stop offset="1" stop-color="#7ee8e0"/></linearGradient>
</defs>
<g clip-path="url(#cv)"><rect width="1000" height="170" fill="#050b1c"/>
<g filter="url(#bl)">
<circle r="100" fill="#2563eb" opacity=".55"><animate attributeName="cx" values="220;340;220" dur="8s" repeatCount="indefinite"/><animate attributeName="cy" values="50;120;50" dur="8s" repeatCount="indefinite"/></circle>
<circle r="90" fill="#14b8a6" opacity=".45"><animate attributeName="cx" values="780;660;780" dur="8s" repeatCount="indefinite"/><animate attributeName="cy" values="120;50;120" dur="8s" repeatCount="indefinite"/></circle>
</g></g>
<rect x=".5" y=".5" width="999" height="169" rx="19.5" fill="none" stroke="#fff" stroke-opacity=".1"/>
<rect x="40" y="20" width="920" height="130" rx="26" fill="#0a1530" fill-opacity=".35"/>
<rect x="40" y="20" width="920" height="130" rx="26" fill="url(#sheen)"/>
<rect x="40.5" y="20.5" width="919" height="129" rx="25.5" fill="none" stroke="url(#edge)"/>
<line x1="74" y1="20.8" x2="926" y2="20.8" stroke="#fff" stroke-opacity=".5" stroke-width="1.5" stroke-linecap="round"/>
<rect x="40.5" y="20.5" width="919" height="129" rx="25.5" fill="none" stroke="url(#beam)" stroke-width="1.6" pathLength="1000" stroke-dasharray="90 910" stroke-linecap="round"><animate attributeName="stroke-dashoffset" values="0;-1000" dur="8s" repeatCount="indefinite"/></rect>
<text x="84" y="56" class="eb">GITHUB</text>{stats}
<text x="{x0}" y="56" class="eb">TOP LANGUAGES</text>{bar}{leg}
</svg>'''

if __name__ == "__main__":
    try:
        data = fetch()
    except Exception as e:
        print("Không lấy được số liệu, giữ nguyên file cũ:", e); sys.exit(0)
    OUT.write_text(build(data), encoding="utf-8")
    print("OK", data)
