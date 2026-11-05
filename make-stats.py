#!/usr/bin/env python3
"""Vẽ github-stats.svg (thẻ kính) từ GitHub API, không phụ thuộc dịch vụ ngoài."""
import base64, html, json, os, pathlib, sys, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "github-stats.svg"
USER = "nhatnam7kz"
COLORS = ["#60a5fa", "#5eead4", "#a78bfa", "#fbbf24", "#f472b6", "#fb923c",
          "#34d399", "#38bdf8", "#e879f9", "#a3e635", "#f87171", "#94a3b8"]  # hết màu thì lặp lại

# Chỉ tính ngôn ngữ lập trình: loại markup / style / dữ liệu / văn bản / build script.
# Thêm hoặc bớt tên tùy ý (tên đúng như GitHub hiển thị). Muốn tính hết thì để set().
EXCLUDE = {"HTML", "CSS", "SCSS", "Sass", "Less", "Jupyter Notebook", "Markdown", "TeX",
           "JSON", "YAML", "XML", "XSLT", "Dockerfile", "Makefile", "CMake", "Batchfile"}
OTHERS = "Others"               # gộp mọi ngôn ngữ có tỉ lệ <= 1% vào mục này
OTHERS_COLOR = "#64748b"
SKIP_REPOS = set()              # tên repo muốn bỏ qua, ví dụ {"ten-repo-bai-tap"}


def get(url):
    h = {"User-Agent": "stats", "Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        h["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=30))


def get_all_repos():
    repos, page = [], 1
    while True:
        batch = get(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner&page={page}")
        repos += batch
        if len(batch) < 100:
            return repos
        page += 1


def fetch():
    u = get(f"https://api.github.com/users/{USER}")
    repos = [r for r in get_all_repos() if not r["fork"] and r["name"] not in SKIP_REPOS]
    langs, failed = {}, 0  # ngôn ngữ -> tổng số byte code trên mọi repo
    for r in repos:
        try:
            for name, nbytes in get(f"https://api.github.com/repos/{USER}/{r['name']}/languages").items():
                langs[name] = langs.get(name, 0) + nbytes
        except Exception as e:
            failed += 1
            print("Bỏ qua repo", r["name"], "-", e)
    if repos and failed > len(repos) // 2:
        raise RuntimeError(f"Quá nhiều repo lỗi ({failed}/{len(repos)}), có thể bị rate limit")

    langs = {n: c for n, c in langs.items() if n not in EXCLUDE}
    ranked = sorted(langs.items(), key=lambda x: -x[1])

    # In toàn bộ để dễ kiểm tra (xem trong log Actions)
    total_all = sum(langs.values()) or 1
    print("--- Chi tiết ngôn ngữ ---")
    for n, c in ranked:
        print(f"{n}: {c} bytes ({c * 100 / total_all:.1f}%)")

    tot = sum(c for _, c in ranked) or 1  # chia theo tổng các ngôn ngữ lập trình, tổng luôn = 100%
    main = [(n, c / tot * 100) for n, c in ranked if c / tot * 100 > 1]
    small = sum(c / tot * 100 for n, c in ranked if c / tot * 100 <= 1)
    if small > 0:
        main.append((OTHERS, small))  # gộp các ngôn ngữ <= 1% thành "Others"
    return dict(repos=len(repos), stars=sum(r["stargazers_count"] for r in repos),
                followers=u["followers"], langs=main)


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
    pos = x0
    for i, (n, p) in enumerate(langs):
        col = OTHERS_COLOR if n == OTHERS else COLORS[i % len(COLORS)]
        w = W * p / 100
        last = i == len(langs) - 1
        seg = (x0 + W - pos) if last else max(w - 2, 1.5)  # đoạn cuối kéo hết đến mép để đủ 100%
        bar += f'<rect x="{pos:.1f}" y="70" width="{seg:.1f}" height="8" rx="4" fill="{col}"/>'
        pos += w
        pct = "<1" if p < 1 else str(round(p))
        label = html.escape(f"{n} {pct}%")
        # legend xếp lưới 2 cột, thêm hàng khi nhiều ngôn ngữ
        lx = x0 + (i % 2) * 175
        ly = 104 + (i // 2) * 20
        leg += (f'<circle cx="{lx + 4}" cy="{ly}" r="4" fill="{col}"/>'
                f'<text x="{lx + 14}" y="{ly + 4}" class="lg">{label}</text>')
    rows = max(1, (len(langs) + 1) // 2)
    CH = max(130, 104 + (rows - 1) * 20 + 6)  # chiều cao thẻ tự giãn theo số hàng legend
    H, CH1 = CH + 40, CH - 1
    dy = (CH - 130) / 2  # đẩy khối thông tin repo xuống để luôn căn giữa theo chiều dọc của thẻ
    if not langs:
        bar = f'<rect x="{x0}" y="70" width="{W}" height="8" rx="4" fill="#fff" fill-opacity=".1"/>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="{H}" viewBox="0 0 1000 {H}">
<defs><style>{css}</style>
<clipPath id="cv"><rect width="1000" height="{H}" rx="20"/></clipPath>
<filter id="bl" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="60"/></filter>
<linearGradient id="sheen" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".13"/><stop offset="1" stop-color="#fff" stop-opacity=".03"/></linearGradient>
<linearGradient id="edge" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".45"/><stop offset=".5" stop-color="#fff" stop-opacity=".08"/><stop offset="1" stop-color="#22d3ee" stop-opacity=".35"/></linearGradient>
<linearGradient id="beam" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#22d3ee"/><stop offset="1" stop-color="#67e8f9"/></linearGradient>
<linearGradient id="num" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff"/><stop offset=".55" stop-color="#c7e0ff"/><stop offset="1" stop-color="#7ee8e0"/></linearGradient>
</defs>
<g clip-path="url(#cv)"><rect width="1000" height="{H}" fill="#050b1c"/>
<g filter="url(#bl)">
<circle r="100" fill="#2563eb" opacity=".55"><animate attributeName="cx" values="220;340;220" dur="8s" repeatCount="indefinite"/><animate attributeName="cy" values="50;120;50" dur="8s" repeatCount="indefinite"/></circle>
<circle r="90" fill="#14b8a6" opacity=".45"><animate attributeName="cx" values="780;660;780" dur="8s" repeatCount="indefinite"/><animate attributeName="cy" values="120;50;120" dur="8s" repeatCount="indefinite"/></circle>
</g></g>
<rect x=".5" y=".5" width="999" height="{H - 1}" rx="19.5" fill="none" stroke="#fff" stroke-opacity=".1"/>
<rect x="40" y="20" width="920" height="{CH}" rx="26" fill="#0a1530" fill-opacity=".35"/>
<rect x="40" y="20" width="920" height="{CH}" rx="26" fill="url(#sheen)"/>
<rect x="40.5" y="20.5" width="919" height="{CH1}" rx="25.5" fill="none" stroke="url(#edge)"/>
<line x1="74" y1="20.8" x2="926" y2="20.8" stroke="#fff" stroke-opacity=".5" stroke-width="1.5" stroke-linecap="round"/>
<rect x="40.5" y="20.5" width="919" height="{CH1}" rx="25.5" fill="none" stroke="url(#beam)" stroke-width="1.6" pathLength="1000" stroke-dasharray="90 910" stroke-linecap="round"><animate attributeName="stroke-dashoffset" values="0;-1000" dur="8s" repeatCount="indefinite"/></rect>
<g transform="translate(0,{dy:g})"><text x="84" y="56" class="eb">GITHUB</text>{stats}</g>
<text x="{x0}" y="56" class="eb">TOP LANGUAGES</text>{bar}{leg}
</svg>'''


if __name__ == "__main__":
    try:
        data = fetch()
    except Exception as e:
        print("LỖI - không lấy được số liệu, giữ nguyên file cũ:", repr(e), file=sys.stderr)
        sys.exit(1)  # báo đỏ trong Actions để bạn biết có lỗi
    OUT.write_text(build(data), encoding="utf-8")
    print("OK", data)
