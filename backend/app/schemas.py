"""Response and request models for the public v0.1 API."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from app.domain import Category


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


class HealthResponse(BaseModel):
    status: Literal["ok"]


class Pricing(BaseModel):
    value: float | None = None
    unit: str | None = None
    summary_zh: str | None = None
    source: str | None = None


class Metric(BaseModel):
    key: str
    label_zh: str
    value: float | None = None
    unit: str | None = None
    source: str | None = None


class ProductListItem(BaseModel):
    id: str
    name: str
    tagline_zh: str
    category: Category
    official_url: str
    github_repo_id: str | None = None


class ProductDetail(BaseModel):
    id: str
    name: str
    tagline_zh: str
    overview_zh: str
    category: Category
    official_url: str
    data_as_of: date
    pricing: Pricing
    metrics: list[Metric]
    github_repo_id: str | None = None
    github_full_name: str | None = None


class ProductPage(BaseModel):
    items: list[ProductListItem]
    page: int
    page_size: int
    total: int


class RankingPeriod(BaseModel):
    month: str
    timezone: str
    label_zh: str
    is_fallback_previous_month: bool
    data_as_of: date | None = None
    range_start: date
    range_end: date
    methodology_zh: str
    empty_reason_zh: str | None = None
    note_zh: str


class MetaResponse(BaseModel):
    categories: list[Category]
    github_ranking_period: RankingPeriod


class RankingItem(BaseModel):
    rank: int
    repo_id: str
    full_name: str
    html_url: str
    tagline_zh: str | None = None
    stars_start: int
    stars_end: int
    net_gain: int
    stars_total: int
    product_id: str | None = None


class MonthlyRankingsResponse(BaseModel):
    period: RankingPeriod
    items: list[RankingItem]
    page: int
    page_size: int
    total: int


class GithubRepoDetail(BaseModel):
    id: str
    full_name: str
    html_url: str
    tagline_zh: str | None = None
    product_id: str | None = None
    stars_total: int | None = None
    data_as_of: date | None = None


class AskRequest(BaseModel):
    target_type: Literal["product", "github_repo"]
    target_id: str = Field(min_length=1, max_length=64)
    question: str = Field(min_length=1, max_length=2000)


class Citation(BaseModel):
    field: str
    source: str | None = None


class AskResponse(BaseModel):
    answer: str
    status: Literal["answered", "insufficient_data", "out_of_scope"]
    citations: list[Citation]
