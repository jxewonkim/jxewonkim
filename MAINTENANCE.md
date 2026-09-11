# Profile maintenance

This repository powers https://github.com/jxewonkim.

- Edit README.md to change the introduction, project descriptions, and skill badges.
- Header artwork is original SVG in assets/, with light and dark variants.
- The contribution images and README statistics cards are generated daily at 05:17 Asia/Seoul. GitHub may delay scheduled jobs.
- Run **Actions → Update profile activity → Run workflow** for a manual refresh.
- The workflow uses the repository's automatic GITHUB_TOKEN; no personal access token is stored.
- Generated images are provided by https://github.com/yoshi389111/github-profile-3d-contrib.
- Action dependencies are pinned to commits. Update the pins deliberately when upgrading.
- No private project names, contact email, credentials, or unverified career claims are included.
- Layout reference: https://github.com/yeuljliyn. Introduction and project descriptions are original and based on this account's public projects.

## Public statistics

`scripts/update_stats.py` uses Python's standard library and the authenticated GitHub CLI. The workflow uses its automatic repository token. It fetches public owned non-fork repositories, deduplicates authored commits on their default branches by SHA, and bins their author timestamps in Asia/Seoul (morning 06–12, daytime 12–18, evening 18–24, night 00–06). Bot commits are excluded. PRs and issues count public authored items; stars and repositories cover public owned non-fork repositories. These counts intentionally differ from the profile's contribution calendar.

The script writes four theme-aware SVGs, aggregate `stats/data.json`, and two text snapshots. It never stores raw commit records or author emails. Incomplete API results fail the refresh instead of replacing cards with partial counts.

## Pinned Gists

Two public Gists are available for GitHub's native **Pinned** area:

- [Coding hours](https://gist.github.com/jxewonkim/3a07352ee738810e9bb77f97e1c93641)
- [GitHub stats](https://gist.github.com/jxewonkim/582d81c1462ca1e5ba4a9bfda8c935e6)

Use **Customize your pins → Gists**, select both, and save. See [GitHub's pinning instructions](https://docs.github.com/en/account-and-profile/how-tos/profile-customization/pinning-items-to-your-profile).

README cards update automatically. The Gists are dated snapshots: the repository's automatic token cannot edit Gists, and no personal token is stored in Actions. To refresh the Gists with your locally authenticated CLI:

```sh
python3 scripts/update_stats.py
gh gist edit 3a07352ee738810e9bb77f97e1c93641 -f coding-hours.txt stats/coding-hours.txt
gh gist edit 582d81c1462ca1e5ba4a9bfda8c935e6 -f github-stats.txt stats/github-stats.txt
```
