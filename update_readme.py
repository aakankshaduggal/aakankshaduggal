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

PINNED_REPOS = [
    "instructlab/sdg",
    "redhat-et/homomorphic-learning",
    "ogx-ai/ogx",
    "redhat-et/time-to-merge-tool",
    "opendatahub-io/skills-registry",
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


def get_top_contributions():
    repo_counts = {}
    for repo in PINNED_REPOS:
        data = api("/search/issues", {
            "q": f"author:{USER}+type:pr+is:merged+repo:{repo}",
            "per_page": "1",
        })
        count = data["total_count"]
        if count > 0:
            repo_counts[repo] = count

    ranked = sorted(repo_counts.items(), key=lambda x: -x[1])
    return ranked


def get_recent_prs():
    data = api("/search/issues", {
        "q": f"author:{USER}+type:pr+is:merged",
        "per_page": "5",
        "sort": "created",
        "order": "desc",
    })
    results = []
    for item in data.get("items", []):
        parts = item["repository_url"].split("/")
        repo = f"{parts[-2]}/{parts[-1]}"
        title = item["title"]
        if len(title) > 60:
            title = title[:57] + "..."
        date = item["created_at"][:10]
        url = item["html_url"]
        results.append((title, repo, date, url))
    return results


def replace_section(readme, tag, content):
    pattern = rf"(<!-- {tag} -->).*?(<!-- /{tag} -->)"
    replacement = rf"\1\n{content}\n\2"
    return re.sub(pattern, replacement, readme, flags=re.DOTALL)


def build_stats_section(profile, pr_count):
    repos = profile["public_repos"]
    followers = profile["followers"]
    return f"**{pr_count}** merged PRs · **{repos}** public repos · **{followers}** followers"


def build_contributions_section(contributions):
    lines = []
    for repo, count in contributions:
        lines.append(f"[`{repo}`](https://github.com/{repo}) | **{count}** PRs")
    header = "Repository | Contributions\n:-- | :--"
    return header + "\n" + "\n".join(lines)


def build_recent_section(prs):
    lines = []
    for title, repo, date, url in prs:
        lines.append(f"[{title}]({url}) | `{repo}` | {date}")
    header = "PR | Repository | Date\n:-- | :-- | :--"
    return header + "\n" + "\n".join(lines)


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    readme_path = os.path.join(script_dir, "README.md")

    with open(readme_path) as f:
        readme = f.read()

    profile = get_profile()
    pr_count = get_merged_pr_count()
    contributions = get_top_contributions()
    recent_prs = get_recent_prs()

    readme = replace_section(readme, "STATS", build_stats_section(profile, pr_count))
    readme = replace_section(readme, "CONTRIBUTIONS", build_contributions_section(contributions))
    readme = replace_section(readme, "RECENT", build_recent_section(recent_prs))

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    readme = replace_section(readme, "UPDATED", f"*Last updated: {now}*")

    with open(readme_path, "w") as f:
        f.write(readme)

    print(f"README updated — {pr_count} PRs, {len(contributions)} repos, {len(recent_prs)} recent PRs")


if __name__ == "__main__":
    main()
