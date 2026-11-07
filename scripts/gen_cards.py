"""Generate self-hosted GitHub profile cards (stats, top languages, pinned repos) as SVG.

Usage: python gen_cards.py <graphql-data.json> <output-dir>
Data comes from the GitHub GraphQL API (see the workflow), so no third-party stats server is needed.
"""
import json
import sys
from html import escape
from pathlib import Path

BG, BORDER, TITLE, TEXT, MUTED, ICON = "#1a1b27", "#2a2e42", "#7aa2f7", "#c0caf5", "#787c99", "#bb9af7"
FONT = "font-family:'Segoe UI',Ubuntu,'Helvetica Neue',sans-serif"
PINNED = ["SambatWidget.Windows", "TmsCaptchaSolver", "MusicPlayer", "MilkDrop"]


def frame(width, height, body, title):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        f'<style>.t{{{FONT};font-weight:600;font-size:18px;fill:{TITLE}}}'
        f'.l{{{FONT};font-size:14px;fill:{TEXT}}}.v{{{FONT};font-weight:700;font-size:14px;fill:{TEXT}}}'
        f'.m{{{FONT};font-size:12.5px;fill:{MUTED}}}'
        f'.f{{opacity:0;animation:in .6s ease-out forwards}}@keyframes in{{to{{opacity:1}}}}</style>'
        f'<rect x=".5" y=".5" rx="10" width="{width - 1}" height="{height - 1}" fill="{BG}" stroke="{BORDER}"/>'
        f'<text x="25" y="38" class="t">{escape(title)}</text>{body}</svg>'
    )


def stats_card(user):
    cc = user["contributionsCollection"]
    public = [r for r in user["repositories"]["nodes"] if not r.get("isPrivate")]
    rows = [
        ("★", "Total stars earned", sum(r["stargazerCount"] for r in public)),
        ("⧗", "Contributions this year", cc["contributionCalendar"]["totalContributions"]),
        ("⇄", "Pull requests", user["pullRequests"]["totalCount"]),
        ("!", "Issues", user["issues"]["totalCount"]),
        ("▣", "Public repositories", len(public)),
    ]
    body = ""
    for i, (icon, label, value) in enumerate(rows):
        y = 72 + i * 25
        body += (
            f'<g class="f" style="animation-delay:{i * 120}ms">'
            f'<text x="25" y="{y}" class="l" style="fill:{ICON}">{icon}</text>'
            f'<text x="48" y="{y}" class="l">{label}:</text>'
            f'<text x="250" y="{y}" class="v">{value:,}</text></g>'
        )
    return frame(450, 200, body, "Samir Dahal's GitHub Stats")


def top_langs_card(user, count=8):
    totals = {}
    for repo in user["repositories"]["nodes"]:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            size, color = totals.get(name, (0, edge["node"]["color"] or MUTED))
            totals[name] = (size + edge["size"], color)
    top = sorted(totals.items(), key=lambda kv: kv[1][0], reverse=True)[:count]
    grand = sum(size for _, (size, _) in top) or 1
    bar, x = "", 25.0
    for name, (size, color) in top:
        w = 300 * size / grand
        bar += f'<rect x="{x:.2f}" y="55" width="{w:.2f}" height="8" fill="{color}"/>'
        x += w
    body = f'<mask id="r"><rect x="25" y="55" width="300" height="8" rx="4" fill="#fff"/></mask><g mask="url(#r)">{bar}</g>'
    for i, (name, (size, color)) in enumerate(top):
        cx, cy = 25 + (i % 2) * 150, 90 + (i // 2) * 25
        body += (
            f'<g class="f" style="animation-delay:{i * 90}ms"><circle cx="{cx + 5}" cy="{cy - 4}" r="5" fill="{color}"/>'
            f'<text x="{cx + 16}" y="{cy}" class="m" style="fill:{TEXT}">{escape(name)} '
            f'<tspan style="fill:{MUTED}">{100 * size / grand:.1f}%</tspan></text></g>'
        )
    return frame(350, 200, body, "Most Used Languages")


def wrap(text, limit=55):
    words, lines, line = (text or "No description").split(), [], ""
    for word in words:
        if len(line) + len(word) + 1 > limit:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    lines.append(line)
    return lines[:2] if len(lines) <= 2 else lines[:1] + [lines[1][: limit - 1] + "…"]


def pin_card(repo):
    desc = "".join(
        f'<text x="25" y="{64 + i * 19}" class="m">{escape(line)}</text>' for i, line in enumerate(wrap(repo["description"]))
    )
    lang = repo["primaryLanguage"] or {"name": "—", "color": MUTED}
    footer = (
        f'<circle cx="30" cy="117" r="6" fill="{lang["color"]}"/>'
        f'<text x="42" y="121" class="m" style="fill:{TEXT}">{escape(lang["name"])}</text>'
        f'<text x="150" y="121" class="m" style="fill:{TEXT}"><tspan style="fill:{ICON}">★</tspan> {repo["stargazerCount"]}</text>'
        f'<text x="210" y="121" class="m" style="fill:{TEXT}"><tspan style="fill:{ICON}">⑂</tspan> {repo["forkCount"]}</text>'
    )
    return frame(400, 140, desc + footer, repo["name"])


def main(data_path, out_dir):
    user = json.loads(Path(data_path).read_text(encoding="utf-8"))["data"]["user"]
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "stats.svg").write_text(stats_card(user), encoding="utf-8")
    (out / "top-langs.svg").write_text(top_langs_card(user), encoding="utf-8")
    repos = {r["name"]: r for r in user["repositories"]["nodes"] if not r.get("isPrivate")}
    for name in PINNED:
        if name in repos:
            (out / f"pin-{name}.svg").write_text(pin_card(repos[name]), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
