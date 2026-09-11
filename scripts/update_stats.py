"""Build public-only profile cards from GitHub data, without extra dependencies."""

import datetime as dt
import html
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
USER = os.environ.get("PROFILE_USER", "jxewonkim")
if not re.fullmatch(r"[A-Za-z0-9-]+", USER):
    raise ValueError("Invalid GitHub username")


def api(endpoint):
    result = subprocess.run(["gh", "api", endpoint], capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise RuntimeError(f"GitHub request failed: {endpoint}")
    return json.loads(result.stdout)


def pages(endpoint):
    separator = "&" if "?" in endpoint else "?"
    for page in range(1, 101):
        entries = api(f"{endpoint}{separator}per_page=100&page={page}")
        if not isinstance(entries, list):
            raise ValueError("Unexpected GitHub response")
        yield from entries
        if len(entries) < 100:
            return
    raise RuntimeError("Pagination limit reached; refusing to publish partial totals")


def search_count(kind):
    data = api("search/issues?" + urlencode({"q": f"author:{USER} is:{kind} is:public", "per_page": 1}))
    if data.get("incomplete_results"):
        raise RuntimeError("Incomplete GitHub search; keeping previous cards")
    return data["total_count"]


def period(hour):
    if 6 <= hour < 12:
        return 0
    if 12 <= hour < 18:
        return 1
    if 18 <= hour < 24:
        return 2
    return 3


def collect():
    repos = [r for r in pages(f"users/{USER}/repos?type=owner") if not r["private"] and not r["fork"]]
    commits = {}
    for repo in repos:
        if not repo.get("size"):
            continue
        route = f"repos/{repo['full_name']}/commits?" + urlencode({"author": USER, "sha": repo["default_branch"]})
        for commit in pages(route):
            # Never include bot commits or a different author returned by the API.
            if (commit.get("author") or {}).get("login", "").lower() != USER.lower():
                continue
            commits[commit["sha"]] = dt.datetime.fromisoformat(commit["commit"]["author"]["date"].replace("Z", "+00:00"))
    counts = [0, 0, 0, 0]
    for authored in commits.values():
        counts[period(authored.astimezone(ZoneInfo("Asia/Seoul")).hour)] += 1
    return {
        "username": USER,
        "updated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "timezone": "Asia/Seoul",
        "scope": "Commits: public owned non-fork repositories, default branches, unique authored commits. PRs/issues: public authored items. Stars/repos: public owned non-fork repositories.",
        "stars": sum(r["stargazers_count"] for r in repos),
        "commits": len(commits), "prs": search_count("pr"), "issues": search_count("issue"),
        "repositories": len(repos), "period_counts": counts,
    }


def title_for(counts):
    if not sum(counts):
        return "My coding hours"
    return ["I'm a morning coder", "I'm a daytime coder", "I'm an evening coder", "I'm a night owl"][counts.index(max(counts))]


def render(data, dark, hours):
    bg, border, text, muted, inset = ("#0d1117", "#30363d", "#e6edf3", "#8b949e", "#161b22") if dark else ("#ffffff", "#d0d7de", "#1f2328", "#656d76", "#f6f8fa")
    title = title_for(data["period_counts"]) if hours else "JAEWON's GitHub Stats"
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="480" height="270" viewBox="0 0 480 270" role="img" aria-labelledby="title desc"><title id="title">{html.escape(title)}</title><desc id="desc">{html.escape(data["scope"])}</desc>',
             f'<rect x="1" y="1" width="478" height="268" rx="12" fill="{bg}" stroke="{border}"/>',
             f'<text x="24" y="39" fill="#58a6ff" font-family="Arial,sans-serif" font-size="18" font-weight="700">{html.escape(title)}</text>',
             f'<rect x="20" y="58" width="440" height="164" rx="8" fill="{inset}"/>']
    if hours:
        total = data["commits"]
        for i, (label, count) in enumerate(zip(["Morning", "Daytime", "Evening", "Night"], data["period_counts"])):
            y = 88 + i * 34
            pct = count / total * 100 if total else 0
            parts += [f'<text x="34" y="{y}" fill="{text}" font-family="monospace" font-size="13">{label}</text>',
                      f'<text x="220" y="{y}" text-anchor="end" fill="{text}" font-family="monospace" font-size="13">{count:,} commits</text>',
                      f'<rect x="236" y="{y-10}" width="126" height="10" rx="2" fill="{border}"/>',
                      f'<rect x="236" y="{y-10}" width="{126*pct/100:.2f}" height="10" rx="2" fill="#58a6ff"/>',
                      f'<text x="446" y="{y}" text-anchor="end" fill="{text}" font-family="monospace" font-size="13">{pct:.1f}%</text>']
    else:
        for i, (label, key) in enumerate([("Total Stars", "stars"), ("Public Commits", "commits"), ("Total PRs", "prs"), ("Total Issues", "issues"), ("Public Repos", "repositories")]):
            y = 84 + i * 28
            parts += [f'<text x="36" y="{y}" fill="{text}" font-family="monospace" font-size="14">{label}</text>',
                      f'<text x="438" y="{y}" text-anchor="end" fill="{text}" font-family="monospace" font-size="14">{data[key]:,}</text>']
    footer = "Public owned repos · default branches · KST" if hours else "Public activity · see scope below"
    parts += [f'<text x="24" y="248" fill="{muted}" font-family="Arial,sans-serif" font-size="11">{footer}</text>', '</svg>']
    return "\n".join(parts) + "\n"


def write_outputs(data):
    output = ROOT / "stats"
    output.mkdir(exist_ok=True)
    (output / "data.json").write_text(json.dumps(data, indent=2) + "\n")
    for dark in [False, True]:
        for hours in [False, True]:
            name = ("hours" if hours else "github") + ("-dark.svg" if dark else "-light.svg")
            (output / name).write_text(render(data, dark, hours))
    total = data["commits"]
    lines = []
    for symbol, name, count in zip(["🌞", "🌇", "🌃", "🌙"], ["Morning", "Daytime", "Evening", "Night"], data["period_counts"]):
        ratio = count / total if total else 0
        blocks = round(ratio * 20)
        lines.append(f"{symbol} {name:<8} {count:>5} commits  {'█'*blocks}{'░'*(20-blocks)}  {ratio*100:5.1f}%")
    scope = f"\n\nSnapshot: {data['updated_at']}\nPublic owned repositories · default branches · authored commits · Asia/Seoul\nCurrent cards: https://github.com/{USER}\n"
    (output / "coding-hours.txt").write_text("\n".join(lines) + scope)
    lines = [f"{icon}  {name:<18} {data[key]:>10,}" for icon, name, key in [
        ("⭐", "Total Stars:", "stars"), ("➕", "Public Commits:", "commits"), ("🔀", "Total PRs:", "prs"), ("🚩", "Total Issues:", "issues"), ("📦", "Public Repos:", "repositories")]]
    (output / "github-stats.txt").write_text("\n".join(lines) + f"\n\nSnapshot: {data['updated_at']}\n{data['scope']}\nCurrent cards: https://github.com/{USER}\n")


if __name__ == "__main__":
    data = collect()
    write_outputs(data)
    print(json.dumps({k: data[k] for k in ["stars", "commits", "prs", "issues", "repositories", "period_counts"]}))
