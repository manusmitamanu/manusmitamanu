import datetime
import json
import os
import urllib.request

USER = "manusmitamanu"
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "stats.svg")


def gql(query, variables=None):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables or {}}).encode(),
        headers={
            "Authorization": "Bearer " + os.environ.get("GITHUB_TOKEN", ""),
            "User-Agent": "profile-stats",
        },
    )
    with urllib.request.urlopen(req) as r:
        data = json.load(r)
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]


def fetch():
    # repos + stars (owned repos; includes private ones if the token can see them)
    repos, stars, cursor = 0, 0, None
    while True:
        d = gql(
            """query($login:String!,$after:String){user(login:$login){
              createdAt
              repositories(first:100, after:$after, ownerAffiliations:OWNER){
                totalCount pageInfo{hasNextPage endCursor}
                nodes{stargazerCount}}}}""",
            {"login": USER, "after": cursor},
        )["user"]
        created = d["createdAt"]
        r = d["repositories"]
        repos = r["totalCount"]
        stars += sum(n["stargazerCount"] for n in r["nodes"])
        if not r["pageInfo"]["hasNextPage"]:
            break
        cursor = r["pageInfo"]["endCursor"]

    # commits + PRs, every year since the account was created
    commits = prs = 0
    for year in range(int(created[:4]), datetime.date.today().year + 1):
        c = gql(
            """query($login:String!,$from:DateTime!,$to:DateTime!){user(login:$login){
              contributionsCollection(from:$from,to:$to){
                totalCommitContributions totalPullRequestContributions}}}""",
            {"login": USER, "from": f"{year}-01-01T00:00:00Z", "to": f"{year}-12-31T23:59:59Z"},
        )["user"]["contributionsCollection"]
        commits += c["totalCommitContributions"]
        prs += c["totalPullRequestContributions"]
    return [repos, stars, commits, prs]


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
