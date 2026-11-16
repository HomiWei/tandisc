"""Shared constants for the v0.1 contract."""

from typing import Literal, get_args

Category = Literal[
    "developer_tools",
    "productivity",
    "ai",
    "infra",
    "design",
    "payment",
    "analytics",
    "communication",
    "other",
]

CATEGORIES: list[str] = list(get_args(Category))

# Product-confirmed wording. Do not paraphrase.
METHODOLOGY_ZH = "净增 = 月末快照 star 减月初快照 star；时区 Asia/Shanghai；数据来自 GitHub 公开接口与我方快照。"

FALLBACK_LABEL_ZH = "上一完整月"
PARTIAL_LABEL_ZH = "本月至今"
COMPLETE_LABEL_ZH = "完整月"
FALLBACK_REASON_INCOMPLETE = "current_month_snapshots_incomplete"

INSUFFICIENT_ANSWER = "当前档案没有这项数据"
OUT_OF_SCOPE_ANSWER = "这个问题超出了产品档案问答的范围。"

EMPTY_NO_SNAPSHOTS_ZH = "尚无 star 快照，无法计算净增。"
EMPTY_BOUNDARIES_ZH = "该月份缺少可用的月初与月末 star 快照，无法计算净增。"

NOTE_EARLY_MONTH_ZH = "每月 1 日至 7 日默认展示上一完整自然月，不计算尚未结束的本月净增。"
NOTE_PARTIAL_ZH = "展示本月 1 日至最新快照的 star 净增。没有快照时条目为空，不改看上一月。"
NOTE_COMPLETE_ZH = "展示该自然月月初快照到月末快照的 star 净增。"
