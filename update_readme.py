#!/usr/bin/env python3
"""Update README.md with live GitHub stats. Stdlib only — no pip installs."""

import json
import os
import re
import urllib.request
from datetime import datetime, timezone


TOKEN = os.environ.get("GITHUB_TOKEN", "")
USER = "aakankshaduggal"
HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": USER}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"

ORGS = [
    ("instructlab", "InstructLab", "Synthetic data generation & LLM alignment"),
    ("redhat-et", "Red Hat Emerging Technologies", "Applied research & tooling"),
    ("ogx-ai", "OGX", "Open-source AI agents"),
    ("exgentic", "Exgentic", "Agentic AI frameworks"),
    ("mlflow", "MLflow", "ML lifecycle & experiment tracking"),
    ("opendatahub-io", "Open Data Hub", "Open source AI/ML platform on Kubernetes"),
]


def api(path, params=None):
    url = f"https://api.github.com{path}"
    if params:
        url += "?" + "&".join(f"{k}={v}" for k, v in params.items())
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def get_profile():
    return api(f"/users/{USER}")


def get_merged_pr_count():
    data = api("/search/issues", {
        "q": f"author:{USER}+type:pr+is:merged",
        "per_page": "1",
    })
    return data["total_count"]


def get_org_contributions():
    return [(org_id, name, desc) for org_id, name, desc in ORGS]


LANG_COLORS = {
    "Python": "#3572A5",
    "Jupyter Notebook": "#DA5B0B",
    "Shell": "#89e051",
    "JavaScript": "#f1e05a",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "TypeScript": "#3178c6",
    "Makefile": "#427819",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "Java": "#b07219",
    "C++": "#f34b7d",
    "C": "#555555",
    "Dockerfile": "#384d54",
    "YAML": "#cb171e",
}

HIDE_LANGS = {"HTML", "CSS", "Makefile", "Dockerfile", "YAML"}


def get_language_stats():
    repos = []
    page = 1
    while True:
        data = api(f"/users/{USER}/repos", {
            "per_page": "100",
            "page": str(page),
            "type": "owner",
        })
        if not data:
            break
        repos.extend(data)
        if len(data) < 100:
            break
        page += 1

    lang_bytes = {}
    for repo in repos:
        if repo.get("fork"):
            continue
        langs = api(f"/repos/{USER}/{repo['name']}/languages")
        for lang, bytes_count in langs.items():
            if lang not in HIDE_LANGS:
                lang_bytes[lang] = lang_bytes.get(lang, 0) + bytes_count

    ranked = sorted(lang_bytes.items(), key=lambda x: -x[1])[:8]
    total = sum(b for _, b in ranked)
    return [(lang, bytes_count / total * 100) for lang, bytes_count in ranked]


def build_langs_svg(langs):
    width = 400
    bar_h = 8
    row_h = 28
    pad_top = 4
    h = pad_top + len(langs) * row_h + 4

    bars = []
    for i, (lang, pct) in enumerate(langs):
        y = pad_top + i * row_h
        color = LANG_COLORS.get(lang, "#8b8b8b")
        bar_w = max(2, pct / 100 * (width - 140))
        bars.append(
            f'  <text x="0" y="{y + 14}" font-size="13" fill="#c9d1d9" '
            f'font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif">'
            f'{lang}</text>'
            f'\n  <rect x="140" y="{y + 4}" width="{bar_w:.1f}" height="{bar_h}" '
            f'rx="4" fill="{color}" />'
            f'\n  <text x="{140 + bar_w + 8}" y="{y + 14}" font-size="12" fill="#8b949e" '
            f'font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif">'
            f'{pct:.1f}%</text>'
        )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{h}">\n'
        + "\n".join(bars)
        + "\n</svg>"
    )
    return svg


def build_langs_section(langs):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    svg_path = os.path.join(script_dir, "langs.svg")
    svg = build_langs_svg(langs)
    with open(svg_path, "w") as f:
        f.write(svg)
    return '<img src="langs.svg" alt="Languages" />'


def replace_section(readme, tag, content):
    pattern = rf"(<!-- {tag} -->).*?(<!-- /{tag} -->)"
    replacement = rf"\1\n{content}\n\2"
    return re.sub(pattern, replacement, readme, flags=re.DOTALL)


def build_stats_section(profile, pr_count):
    repos = profile["public_repos"]
    followers = profile["followers"]
    return f"**{pr_count}** merged PRs · **{repos}** public repos · **{followers}** followers"


def build_contributions_section(orgs):
    lines = []
    for org_id, name, desc in orgs:
        lines.append(f"[**{name}**](https://github.com/{org_id}) — {desc}")
    return "\n\n".join(lines)


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    readme_path = os.path.join(script_dir, "README.md")

    with open(readme_path) as f:
        readme = f.read()

    profile = get_profile()
    pr_count = get_merged_pr_count()
    orgs = get_org_contributions()

    langs = get_language_stats()

    readme = replace_section(readme, "STATS", build_stats_section(profile, pr_count))
    readme = replace_section(readme, "CONTRIBUTIONS", build_contributions_section(orgs))
    readme = replace_section(readme, "LANGS", build_langs_section(langs))

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    readme = replace_section(readme, "UPDATED", f"*Last updated: {now}*")

    with open(readme_path, "w") as f:
        f.write(readme)

    print(f"README updated — {pr_count} PRs, {len(orgs)} orgs")


if __name__ == "__main__":
    main()
