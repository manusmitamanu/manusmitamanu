"""Builds assets/stats.svg from GitHub's GraphQL API.

Needs a secret called STATS_TOKEN (a classic token with the `repo` scope).
Only totals are written to the SVG. No repository names ever leave this script.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

USER = "manusmitamanu"
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "stats.svg")
URL = "https://api.github.com/graphql"


def gql(query, variables=None):
    token = os.environ.get("STATS_TOKEN", "").strip()
    if not token:
        sys.exit("STATS_TOKEN is not set. Add it under Settings > Secrets and variables > Actions.")
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    for attempt in range(4):
        req = urllib.request.Request(
            URL,
            data=body,
            headers={"Authorization": "Bearer " + token, "User-Agent": "profile-stats"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.load(r)
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:300]
            if e.code in (500, 502, 503, 504) and attempt < 3:
                time.sleep(2 ** (attempt + 1))
                continue
            sys.exit(f"GitHub API returned HTTP {e.code}: {detail}")
        except urllib.error.URLError as e:
            if attempt < 3:
                time.sleep(2 ** (attempt + 1))
                continue
            sys.exit(f"Could not reach GitHub: {e}")
        if data.get("errors"):
            sys.exit("GraphQL error: " + json.dumps(data["errors"])[:500])
        return data["data"]


def fetch():
    # 1) repositories you own (public + private) and their stars
    repos = stars = 0
    cursor = None
    while True:
        u = gql(
            """query($login:String!,$after:String){user(login:$login){
                 id
                 repositories(first:100, after:$after, ownerAffiliations:[OWNER]){
                   totalCount
                   pageInfo{hasNextPage endCursor}
                   nodes{stargazerCount}}}}""",
            {"login": USER, "after": cursor},
        )["user"]
        user_id = u["id"]
        r = u["repositories"]
        repos = r["totalCount"]
        stars += sum(n["stargazerCount"] for n in r["nodes"])
        if not r["pageInfo"]["hasNextPage"]:
            break
        cursor = r["pageInfo"]["endCursor"]

    # 2) commits you authored on the default branch of every repo you can access
    commits = 0
    cursor = None
    while True:
        u = gql(
            """query($login:String!,$uid:ID!,$after:String){user(login:$login){
                 repositories(first:50, after:$after, isFork:false,
                   ownerAffiliations:[OWNER,COLLABORATOR,ORGANIZATION_MEMBER]){
                   pageInfo{hasNextPage endCursor}
                   nodes{defaultBranchRef{target{... on Commit{
                     history(author:{id:$uid}){totalCount}}}}}}}}""",
            {"login": USER, "uid": user_id, "after": cursor},
        )["user"]["repositories"]
        for n in u["nodes"]:
            ref = n.get("defaultBranchRef")  # empty repos have no default branch
            if ref and ref.get("target"):
                commits += ref["target"]["history"]["totalCount"]
        if not u["pageInfo"]["hasNextPage"]:
            break
        cursor = u["pageInfo"]["endCursor"]

    # 3) pull requests you opened, all time
    prs = gql(
        """query($login:String!){user(login:$login){pullRequests{totalCount}}}""",
        {"login": USER},
    )["user"]["pullRequests"]["totalCount"]

    print(f"repositories={repos} stars={stars} commits={commits} pull_requests={prs}")
    return [repos, stars, commits, prs]


def render(values):
    labels = ["repositories", "stars", "commits", "pull requests"]
    cols = ""
    for i, (v, label) in enumerate(zip(values, labels)):
        x = 36 + i * 140
        shown = f"{v:,}" if isinstance(v, int) else v
        cols += (
            f'<text x="{x}" y="104" font-family="Lora, Georgia, serif" font-size="36" fill="#F3E5DC">{shown}</text>\n'
            f'  <text x="{x}" y="128" font-family="Mulish, \'Work Sans\', \'Segoe UI\', Arial, sans-serif" font-size="13" fill="#D9A0AA">{label}</text>\n  '
        )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 160" width="600" height="160" role="img" aria-label="GitHub stats">
  <rect x="0.5" y="0.5" width="599" height="159" rx="14" fill="#160B10" stroke="#8B263D" stroke-opacity="0.7"/>
  <text x="36" y="46" font-family="Lora, Georgia, serif" font-size="17" font-style="italic" fill="#D9A0AA">the numbers, such as they are</text>
  <line x1="36" y1="60" x2="84" y2="60" stroke="#8B263D" stroke-width="2.5" stroke-linecap="round"/>
  {cols}</svg>
'''


if __name__ == "__main__":
    values = fetch()  # exits with an error (and writes nothing) if anything fails
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(render(values))
