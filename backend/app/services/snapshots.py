"""Daily star-snapshot job stub.

Importing or booting the API does not call GitHub and does not require
GITHUB_TOKEN. A later scheduler can call `run_daily_snapshot` with the token.
Snapshots must be dated in APP_TIMEZONE (default Asia/Shanghai): `snapshot_date`
is that calendar date, and `captured_at` is the capture time.

Ranking rules live in app.services.ranking and only read github_star_snapshots.
This stub does not write rows and does not compute net_gain.
"""

from __future__ import annotations


def run_daily_snapshot(github_token: str | None) -> dict[str, str]:
    token = (github_token or "").strip()
    if not token:
        return {"status": "skipped", "reason": "GITHUB_TOKEN unset"}
    return {
        "status": "not_implemented",
        "reason": "P0 skeleton does not call the GitHub API",
    }
