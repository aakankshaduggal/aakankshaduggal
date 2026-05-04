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


def check_org_contributions():
    active_orgs = []
    for org_id, name, desc in ORGS:
        data = api("/search/issues", {
            "q": f"author:{USER}+type:pr+is:merged+org:{org_id}",
            "per_page": "1",
        })
        if data["total_count"] > 0:
            active_orgs.append((org_id, name, desc))
    return active_orgs


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
    orgs = check_org_contributions()

    readme = replace_section(readme, "STATS", build_stats_section(profile, pr_count))
    readme = replace_section(readme, "CONTRIBUTIONS", build_contributions_section(orgs))

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    readme = replace_section(readme, "UPDATED", f"*Last updated: {now}*")

    with open(readme_path, "w") as f:
        f.write(readme)

    print(f"README updated — {pr_count} PRs, {len(orgs)} orgs")


if __name__ == "__main__":
    main()
