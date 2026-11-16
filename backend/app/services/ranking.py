"""GitHub monthly net-gain ranking.

Rules confirmed 2026-11-16, timezone from settings (default Asia/Shanghai):

- net_gain = end snapshot stars - start snapshot stars
- Start snapshot: the row dated the 1st of the month, else the latest snapshot
  captured before that day's 00:00
- End snapshot for a finished month: the row dated the last day, else the latest
  snapshot captured before the next month's 00:00
- Days 1-7 of the current month: default to the previous complete month
  (is_fallback_previous_month=true, label 上一完整月)
- From day 8: default to month-start through the latest snapshot. If that window
  cannot be computed for any repo, fall back to the previous complete month.
- Never invent net_gain. Repos without a usable pair are omitted. If none remain,
  items is empty and the period explains why.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.domain import (
    COMPLETE_LABEL_ZH,
    EMPTY_BOUNDARIES_ZH,
    EMPTY_NO_SNAPSHOTS_ZH,
    FALLBACK_LABEL_ZH,
    METHODOLOGY_ZH,
    NOTE_COMPLETE_ZH,
    NOTE_EARLY_MONTH_ZH,
    NOTE_FALLBACK_INSUFFICIENT_ZH,
    NOTE_PARTIAL_ZH,
    PARTIAL_LABEL_ZH,
)
from app.schemas import RankingItem, RankingPeriod
from app.services import clock


class MonthNotAvailable(Exception):
    pass


@dataclass(frozen=True)
class SnapshotPoint:
    repo_id: str
    snapshot_date: date
    stars: int
    captured_at: datetime


@dataclass(frozen=True)
class RepoInput:
    id: str
    full_name: str
    html_url: str
    tagline_zh: str | None
    product_id: str | None


@dataclass(frozen=True)
class RankedRepo:
    item: RankingItem
    end_date: date


def _aware(value: datetime, tz: ZoneInfo) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=tz)
    return value.astimezone(tz)


def month_start(day: date) -> date:
    return day.replace(day=1)


def previous_month(first: date) -> date:
    return (first - timedelta(days=1)).replace(day=1)


def month_window(first: date) -> tuple[date, date, date]:
    if first.month == 12:
        nxt = date(first.year + 1, 1, 1)
    else:
        nxt = date(first.year, first.month + 1, 1)
    last = nxt - timedelta(days=1)
    return first, last, nxt


def _boundary(day: date, tz: ZoneInfo) -> datetime:
    return datetime(day.year, day.month, day.day, 0, 0, tzinfo=tz)


def select_start(points: list[SnapshotPoint], first: date, tz: ZoneInfo) -> SnapshotPoint | None:
    on_first = [point for point in points if point.snapshot_date == first]
    if on_first:
        return max(on_first, key=lambda point: _aware(point.captured_at, tz))
    boundary = _boundary(first, tz)
    before = [point for point in points if _aware(point.captured_at, tz) < boundary]
    if not before:
        return None
    return max(before, key=lambda point: _aware(point.captured_at, tz))


def select_end_complete(
    points: list[SnapshotPoint],
    last: date,
    next_first: date,
    tz: ZoneInfo,
) -> SnapshotPoint | None:
    next_boundary = _boundary(next_first, tz)
    on_last = [
        point
        for point in points
        if point.snapshot_date == last and _aware(point.captured_at, tz) < next_boundary
    ]
    if on_last:
        return max(on_last, key=lambda point: _aware(point.captured_at, tz))
    before = [point for point in points if _aware(point.captured_at, tz) < next_boundary]
    if not before:
        return None
    return max(before, key=lambda point: _aware(point.captured_at, tz))


def select_end_partial(
    points: list[SnapshotPoint],
    first: date,
    now: datetime,
    tz: ZoneInfo,
) -> SnapshotPoint | None:
    now_local = _aware(now, tz)
    eligible = [
        point
        for point in points
        if point.snapshot_date >= first and _aware(point.captured_at, tz) <= now_local
    ]
    if not eligible:
        return None
    return max(eligible, key=lambda point: _aware(point.captured_at, tz))


def _pair_ok(start: SnapshotPoint | None, end: SnapshotPoint | None) -> bool:
    if start is None or end is None:
        return False
    # A single observation is not a start/end pair, so net_gain is not invented as 0.
    return end.snapshot_date > start.snapshot_date


def compute_month_items(
    repos: list[RepoInput],
    snapshots: list[SnapshotPoint],
    first: date,
    mode: str,
    tz: ZoneInfo,
    now: datetime,
) -> list[RankedRepo]:
    grouped: dict[str, list[SnapshotPoint]] = {}
    for point in snapshots:
        grouped.setdefault(point.repo_id, []).append(point)
    _first, last, nxt = month_window(first)
    ranked: list[RankedRepo] = []
    for repo in repos:
        points = grouped.get(repo.id, [])
        start = select_start(points, first, tz)
        if mode == "complete":
            end = select_end_complete(points, last, nxt, tz)
        else:
            end = select_end_partial(points, first, now, tz)
        if end is not None and end.snapshot_date < first:
            end = None
        if not _pair_ok(start, end):
            continue
        assert start is not None and end is not None
        ranked.append(
            RankedRepo(
                item=RankingItem(
                    rank=0,
                    repo_id=repo.id,
                    full_name=repo.full_name,
                    html_url=repo.html_url,
                    tagline_zh=repo.tagline_zh,
                    stars_start=start.stars,
                    stars_end=end.stars,
                    net_gain=end.stars - start.stars,
                    stars_total=end.stars,
                    product_id=repo.product_id,
                ),
                end_date=end.snapshot_date,
            )
        )
    ranked.sort(key=lambda row: (-row.item.net_gain, row.item.repo_id))
    assigned: list[RankedRepo] = []
    for index, row in enumerate(ranked, start=1):
        assigned.append(RankedRepo(item=row.item.model_copy(update={"rank": index}), end_date=row.end_date))
    return assigned


def _empty_reason(snapshots: list[SnapshotPoint], items: list[RankingItem]) -> str | None:
    if items:
        return None
    if not snapshots:
        return EMPTY_NO_SNAPSHOTS_ZH
    return EMPTY_BOUNDARIES_ZH


def _build_period(
    *,
    first: date,
    mode: str,
    today: date,
    tz_name: str,
    fallback: bool,
    note_zh: str,
    ranked: list[RankedRepo],
    snapshots: list[SnapshotPoint],
) -> RankingPeriod:
    _first, last, _nxt = month_window(first)
    items = [row.item for row in ranked]
    data_as_of = max((row.end_date for row in ranked), default=None)
    if mode == "partial":
        range_end = data_as_of or today
    else:
        range_end = last
    if fallback:
        label = FALLBACK_LABEL_ZH
    elif mode == "partial":
        label = PARTIAL_LABEL_ZH
    else:
        label = COMPLETE_LABEL_ZH
    return RankingPeriod(
        month=f"{first.year:04d}-{first.month:02d}",
        timezone=tz_name,
        label_zh=label,
        is_fallback_previous_month=fallback,
        data_as_of=data_as_of,
        range_start=first,
        range_end=range_end,
        methodology_zh=METHODOLOGY_ZH,
        empty_reason_zh=_empty_reason(snapshots, items),
        note_zh=note_zh,
    )


def _cutoff(today: date, tz: ZoneInfo) -> datetime:
    live = _aware(clock.now(tz), tz)
    if live.date() == today:
        return live
    return datetime(today.year, today.month, today.day, 23, 59, tzinfo=tz)


def resolve_rankings(
    *,
    today: date,
    repos: list[RepoInput],
    snapshots: list[SnapshotPoint],
    tz: ZoneInfo,
    month: str | None,
) -> tuple[RankingPeriod, list[RankingItem]]:
    now = _cutoff(today, tz)
    tz_name = getattr(tz, "key", None) or str(tz)

    if month is not None:
        first = _parse_month(month)
        current = month_start(today)
        if first > current:
            raise MonthNotAvailable("不能查询未来的月份")
        mode = "complete" if first < current else "partial"
        note = NOTE_PARTIAL_ZH if mode == "partial" else NOTE_COMPLETE_ZH
        ranked = compute_month_items(repos, snapshots, first, mode, tz, now)
        period = _build_period(
            first=first,
            mode=mode,
            today=today,
            tz_name=tz_name,
            fallback=False,
            note_zh=note,
            ranked=ranked,
            snapshots=snapshots,
        )
        return period, [row.item for row in ranked]

    current = month_start(today)
    if today.day <= 7:
        first = previous_month(current)
        ranked = compute_month_items(repos, snapshots, first, "complete", tz, now)
        period = _build_period(
            first=first,
            mode="complete",
            today=today,
            tz_name=tz_name,
            fallback=True,
            note_zh=NOTE_EARLY_MONTH_ZH,
            ranked=ranked,
            snapshots=snapshots,
        )
        return period, [row.item for row in ranked]

    ranked = compute_month_items(repos, snapshots, current, "partial", tz, now)
    if ranked:
        period = _build_period(
            first=current,
            mode="partial",
            today=today,
            tz_name=tz_name,
            fallback=False,
            note_zh=NOTE_PARTIAL_ZH,
            ranked=ranked,
            snapshots=snapshots,
        )
        return period, [row.item for row in ranked]

    first = previous_month(current)
    ranked = compute_month_items(repos, snapshots, first, "complete", tz, now)
    period = _build_period(
        first=first,
        mode="complete",
        today=today,
        tz_name=tz_name,
        fallback=True,
        note_zh=NOTE_FALLBACK_INSUFFICIENT_ZH,
        ranked=ranked,
        snapshots=snapshots,
    )
    return period, [row.item for row in ranked]


def _parse_month(value: str) -> date:
    try:
        year_s, month_s = value.split("-")
        year, month = int(year_s), int(month_s)
        if month < 1 or month > 12:
            raise ValueError
        return date(year, month, 1)
    except ValueError as exc:
        raise MonthNotAvailable("month 需要是 YYYY-MM") from exc


def today_in(tz: ZoneInfo) -> date:
    return clock.now(tz).date()
