from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from app.domain import FALLBACK_LABEL_ZH, METHODOLOGY_ZH, PARTIAL_LABEL_ZH
from app.services.ranking import (
    MonthNotAvailable,
    RepoInput,
    SnapshotPoint,
    resolve_rankings,
)

TZ = ZoneInfo("Asia/Shanghai")


def freeze(monkeypatch, day: date, hour: int = 18) -> None:
    monkeypatch.setattr(
        "app.services.clock.now",
        lambda tz: datetime(day.year, day.month, day.day, hour, 0, tzinfo=tz),
    )


def point(repo_id: str, day: str, stars: int, hour: int = 12) -> SnapshotPoint:
    snapshot_day = date.fromisoformat(day)
    return SnapshotPoint(
        repo_id=repo_id,
        snapshot_date=snapshot_day,
        stars=stars,
        captured_at=datetime(snapshot_day.year, snapshot_day.month, snapshot_day.day, hour, 0, tzinfo=TZ),
    )


def repo(repo_id: str, product_id: str | None = None) -> RepoInput:
    return RepoInput(
        id=repo_id,
        full_name=f"acme/{repo_id}",
        html_url=f"https://github.com/acme/{repo_id}",
        tagline_zh="示例仓库",
        product_id=product_id,
    )


def test_no_snapshots_on_nov_16_uses_current_month(monkeypatch):
    today = date(2026, 11, 16)
    freeze(monkeypatch, today)
    period, items = resolve_rankings(today=today, repos=[], snapshots=[], tz=TZ, month=None)
    assert items == []
    assert period.month == "2026-11"
    assert period.is_fallback_previous_month is False
    assert period.label_zh == PARTIAL_LABEL_ZH
    assert period.label_zh == "本月至今"
    assert period.data_as_of is None
    assert period.methodology_zh == METHODOLOGY_ZH
    assert period.empty_reason_zh == "尚无 star 快照，无法计算净增。"
    assert period.range_start == date(2026, 11, 1)
    assert period.range_end == date(2026, 11, 16)
    assert period.timezone == "Asia/Shanghai"
    assert period.fallback_reason is None
    dumped = period.model_dump(by_alias=True)
    assert dumped["year_month"] == "2026-11"
    assert dumped["start_date"] == date(2026, 11, 1)
    assert dumped["end_date"] == date(2026, 11, 16)
    assert "month" not in dumped
    assert "range_start" not in dumped
    assert "range_end" not in dumped


def test_days_1_to_7_with_no_snapshots_use_previous_month(monkeypatch):
    today = date(2026, 11, 3)
    freeze(monkeypatch, today)
    period, items = resolve_rankings(today=today, repos=[], snapshots=[], tz=TZ, month=None)
    assert items == []
    assert period.month == "2026-10"
    assert period.is_fallback_previous_month is True
    assert period.label_zh == FALLBACK_LABEL_ZH
    assert period.label_zh == "上一完整月"
    assert period.data_as_of is None
    assert period.range_start == date(2026, 10, 1)
    assert period.range_end == date(2026, 10, 31)
    assert period.fallback_reason == "current_month_snapshots_incomplete"


def test_days_1_to_7_use_previous_month_even_when_current_has_snapshots(monkeypatch):
    today = date(2026, 11, 3)
    freeze(monkeypatch, today)
    snapshots = [
        point("gh_a", "2026-10-01", 10, hour=1),
        point("gh_a", "2026-10-31", 40, hour=1),
        point("gh_a", "2026-11-01", 40, hour=1),
        point("gh_a", "2026-11-03", 90, hour=1),
    ]
    period, items = resolve_rankings(
        today=today, repos=[repo("gh_a", "prd_a")], snapshots=snapshots, tz=TZ, month=None
    )
    assert period.month == "2026-10"
    assert period.is_fallback_previous_month is True
    assert period.fallback_reason == "current_month_snapshots_incomplete"
    assert len(items) == 1
    assert items[0].net_gain == 30
    assert items[0].stars_start == 10
    assert items[0].stars_end == 40


def test_from_day_8_uses_latest_snapshot_in_the_current_month(monkeypatch):
    today = date(2026, 11, 16)
    freeze(monkeypatch, today, hour=18)
    snapshots = [
        point("gh_a", "2026-10-31", 100, hour=23),
        point("gh_a", "2026-11-01", 110, hour=1),
        point("gh_a", "2026-11-16", 150, hour=9),
        point("gh_a", "2026-11-20", 999, hour=1),
    ]
    period, items = resolve_rankings(
        today=today, repos=[repo("gh_a", "prd_a")], snapshots=snapshots, tz=TZ, month=None
    )
    assert period.month == "2026-11"
    assert period.is_fallback_previous_month is False
    assert period.label_zh == PARTIAL_LABEL_ZH
    assert period.data_as_of == date(2026, 11, 16)
    assert items[0].stars_start == 110
    assert items[0].stars_end == 150
    assert items[0].net_gain == 40
    assert items[0].stars_total == 150
    assert items[0].product_id == "prd_a"


def test_day_8_without_current_snapshots_stays_on_current_month(monkeypatch):
    today = date(2026, 11, 8)
    freeze(monkeypatch, today)
    snapshots = [
        point("gh_a", "2026-10-01", 5, hour=1),
        point("gh_a", "2026-10-31", 9, hour=1),
    ]
    period, items = resolve_rankings(
        today=today, repos=[repo("gh_a")], snapshots=snapshots, tz=TZ, month=None
    )
    assert items == []
    assert period.month == "2026-11"
    assert period.is_fallback_previous_month is False
    assert period.fallback_reason is None
    assert period.label_zh == PARTIAL_LABEL_ZH
    assert period.data_as_of is None


def test_complete_month_prefers_first_and_last_day(monkeypatch):
    today = date(2026, 11, 16)
    freeze(monkeypatch, today)
    snapshots = [
        point("gh_a", "2026-09-30", 100, hour=23),
        point("gh_a", "2026-10-01", 110, hour=1),
        point("gh_a", "2026-10-15", 120, hour=12),
        point("gh_a", "2026-10-31", 150, hour=22),
        point("gh_a", "2026-11-01", 999, hour=0),
    ]
    period, items = resolve_rankings(
        today=today, repos=[repo("gh_a")], snapshots=snapshots, tz=TZ, month="2026-10"
    )
    assert period.is_fallback_previous_month is False
    assert period.month == "2026-10"
    assert items[0].stars_start == 110
    assert items[0].stars_end == 150
    assert items[0].net_gain == 40


def test_start_uses_latest_snapshot_before_month_when_first_is_missing(monkeypatch):
    today = date(2026, 11, 16)
    freeze(monkeypatch, today)
    snapshots = [
        point("gh_a", "2026-09-28", 80, hour=12),
        point("gh_a", "2026-09-30", 90, hour=23),
        point("gh_a", "2026-10-31", 130, hour=20),
    ]
    _period, items = resolve_rankings(
        today=today, repos=[repo("gh_a")], snapshots=snapshots, tz=TZ, month="2026-10"
    )
    assert items[0].stars_start == 90
    assert items[0].stars_end == 130
    assert items[0].net_gain == 40


def test_end_uses_latest_snapshot_before_next_month_when_last_day_is_missing(monkeypatch):
    today = date(2026, 11, 16)
    freeze(monkeypatch, today)
    snapshots = [
        point("gh_a", "2026-10-01", 10, hour=1),
        point("gh_a", "2026-10-20", 18, hour=8),
        point("gh_a", "2026-11-01", 500, hour=0),
    ]
    _period, items = resolve_rankings(
        today=today, repos=[repo("gh_a")], snapshots=snapshots, tz=TZ, month="2026-10"
    )
    assert items[0].stars_end == 18
    assert items[0].net_gain == 8


def test_single_snapshot_does_not_invent_zero_gain(monkeypatch):
    today = date(2026, 11, 16)
    freeze(monkeypatch, today)
    snapshots = [point("gh_a", "2026-10-15", 10)]
    period, items = resolve_rankings(
        today=today, repos=[repo("gh_a")], snapshots=snapshots, tz=TZ, month="2026-10"
    )
    assert items == []
    assert period.empty_reason_zh == "该月份缺少可用的月初与月末 star 快照，无法计算净增。"


def test_rank_orders_by_net_gain_then_repo_id(monkeypatch):
    today = date(2026, 11, 16)
    freeze(monkeypatch, today)
    snapshots = [
        point("gh_b", "2026-10-01", 10),
        point("gh_b", "2026-10-31", 15),
        point("gh_a", "2026-10-01", 10),
        point("gh_a", "2026-10-31", 15),
        point("gh_c", "2026-10-01", 10),
        point("gh_c", "2026-10-31", 40),
    ]
    _period, items = resolve_rankings(
        today=today,
        repos=[repo("gh_b"), repo("gh_a"), repo("gh_c")],
        snapshots=snapshots,
        tz=TZ,
        month="2026-10",
    )
    assert [(item.rank, item.repo_id, item.net_gain) for item in items] == [
        (1, "gh_c", 30),
        (2, "gh_a", 5),
        (3, "gh_b", 5),
    ]


def test_future_month_is_rejected(monkeypatch):
    today = date(2026, 11, 16)
    freeze(monkeypatch, today)
    with pytest.raises(MonthNotAvailable):
        resolve_rankings(today=today, repos=[], snapshots=[], tz=TZ, month="2026-12")
