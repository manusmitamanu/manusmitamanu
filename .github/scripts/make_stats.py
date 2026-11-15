import json
import os
import urllib.request

USER = "manusmitamanu"
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "stats.svg")


def api(path):
    req = urllib.request.Request(
        "https://api.github.com" + path,
        headers={
            "Authorization": "Bearer " + os.environ.get("GITHUB_TOKEN", ""),
            "Accept": "application/vnd.github+json",
            "User-Agent": "profile-stats",
        },
    )
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def fetch():
    user = api(f"/users/{USER}")
    stars, page = 0, 1
    while True:
        repos = api(f"/users/{USER}/repos?per_page=100&page={page}")
        if not repos:
            break
        stars += sum(r["stargazers_count"] for r in repos)
        page += 1
    commits = api(f"/search/commits?q=author:{USER}&per_page=1")["total_count"]
    prs = api(f"/search/issues?q=author:{USER}+type:pr&per_page=1")["total_count"]
    return [user["public_repos"], stars, commits, prs]


def render(values):
    labels = ["repositories", "stars", "commits", "pull requests"]
    cols = ""
    for i, (v, l) in enumerate(zip(values, labels)):
        x = 36 + i * 140
        cols += (
            f'<text x="{x}" y="104" font-family="Lora, Georgia, serif" font-size="36" fill="#F3E5DC">{v}</text>\n'
            f'  <text x="{x}" y="128" font-family="Mulish, \'Work Sans\', \'Segoe UI\', Arial, sans-serif" font-size="13" fill="#D9A0AA">{l}</text>\n  '
        )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 160" width="600" height="160" role="img" aria-label="GitHub stats">
  <rect x="0.5" y="0.5" width="599" height="159" rx="14" fill="#160B10" stroke="#8B263D" stroke-opacity="0.7"/>
  <text x="36" y="46" font-family="Lora, Georgia, serif" font-size="17" font-style="italic" fill="#D9A0AA">the numbers, such as they are</text>
  <line x1="36" y1="60" x2="84" y2="60" stroke="#8B263D" stroke-width="2.5" stroke-linecap="round"/>
  {cols}</svg>
'''


if __name__ == "__main__":
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(render(fetch()))
