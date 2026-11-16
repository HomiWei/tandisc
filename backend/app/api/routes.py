"""Public v0.1 routes. No authentication on this skeleton."""

import logging
import re
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.domain import CATEGORIES
from app.errors import AppError
from app.models import GithubRepo, Product
from app.queries import as_date, latest_snapshot, product_record, ranking_inputs, repo_record
from app.schemas import (
    AskRequest,
    AskResponse,
    GithubRepoDetail,
    HealthResponse,
    MetaResponse,
    MonthlyRankingsResponse,
    ProductDetail,
    ProductPage,
    RankingItem,
)
from app.serialize import product_detail, product_list_item
from app.services.ask import answer_question
from app.services.ranking import MonthNotAvailable, resolve_rankings, today_in

logger = logging.getLogger("tandisc.api")
router = APIRouter()

CategoryQuery = Annotated[str | None, Query()]
PageQuery = Annotated[int, Query(ge=1, le=100_000)]
ProductPageSize = Annotated[int, Query(ge=1, le=50)]
RankingPageSize = Annotated[int, Query(ge=1, le=50)]
SortQuery = Annotated[str, Query(pattern=r"^(display_order|name)$")]


def get_session(request: Request):
    session = request.app.state.session_factory()
    try:
        yield session
    finally:
        session.close()


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def _like_contains(term: str) -> str:
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/api/v1/meta", response_model=MetaResponse)
def meta(session: Session = Depends(get_session), settings: Settings = Depends(get_settings)) -> MetaResponse:
    period, _items = _rankings(session, settings, month=None)
    return MetaResponse(categories=list(CATEGORIES), github_ranking_period=period)


@router.get("/api/v1/products", response_model=ProductPage)
def list_products(
    category: CategoryQuery = None,
    q: Annotated[str | None, Query(max_length=100)] = None,
    sort: SortQuery = "display_order",
    page: PageQuery = 1,
    page_size: ProductPageSize = 30,
    session: Session = Depends(get_session),
) -> ProductPage:
    if category is not None and category not in CATEGORIES:
        raise AppError(400, "VALIDATION_ERROR", "category 不在允许的枚举内")
    filters = []
    if category is not None:
        filters.append(Product.category == category)
    if q is not None and q.strip():
        filters.append(Product.name.ilike(_like_contains(q.strip()), escape="\\"))
    total = session.scalar(select(func.count()).select_from(Product).where(*filters)) or 0
    order = [Product.display_order.asc(), Product.id.asc()]
    if sort == "name":
        order = [Product.name.asc(), Product.id.asc()]
    rows = session.scalars(
        select(Product).where(*filters).order_by(*order).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return ProductPage(
        items=[product_list_item(row) for row in rows],
        page=page,
        page_size=page_size,
        total=int(total),
    )


@router.get("/api/v1/products/{product_id}", response_model=ProductDetail)
def get_product(product_id: str, session: Session = Depends(get_session)) -> ProductDetail:
    product = session.get(Product, product_id)
    if product is None:
        raise AppError(404, "NOT_FOUND", "产品不存在")
    full_name = None
    if product.github_repo_id:
        repo = session.get(GithubRepo, product.github_repo_id)
        if repo is not None:
            full_name = repo.full_name
    return product_detail(product, full_name)


@router.get("/api/v1/github/monthly-rankings", response_model=MonthlyRankingsResponse)
def monthly_rankings(
    month: Annotated[str | None, Query()] = None,
    page: PageQuery = 1,
    page_size: RankingPageSize = 50,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> MonthlyRankingsResponse:
    if month is not None and re.fullmatch(r"\d{4}-\d{2}", month) is None:
        raise AppError(400, "VALIDATION_ERROR", "month 需要是 YYYY-MM")
    period, items = _rankings(session, settings, month=month)
    total = len(items)
    start = (page - 1) * page_size
    page_items: list[RankingItem] = items[start : start + page_size]
    logger.info(
        "monthly rankings month=%s fallback=%s total=%s",
        period.month,
        period.is_fallback_previous_month,
        total,
    )
    return MonthlyRankingsResponse(
        period=period,
        items=page_items,
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/api/v1/github/repos/{repo_id}", response_model=GithubRepoDetail)
def get_repo(
    repo_id: str,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> GithubRepoDetail:
    repo = session.get(GithubRepo, repo_id)
    if repo is None:
        raise AppError(404, "NOT_FOUND", "仓库不存在")
    product_id = session.scalar(select(Product.id).where(Product.github_repo_id == repo.id))
    snapshot = latest_snapshot(session, repo.id, settings.zoneinfo)
    stars_total = None if snapshot is None else int(snapshot.stars)
    data_as_of = None if snapshot is None else as_date(snapshot.snapshot_date)
    return GithubRepoDetail(
        id=repo.id,
        full_name=repo.full_name,
        html_url=repo.html_url,
        tagline_zh=repo.tagline_zh,
        product_id=product_id,
        stars_total=stars_total,
        data_as_of=data_as_of,
    )


@router.post("/api/v1/ask", response_model=AskResponse)
def ask(
    body: AskRequest,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> AskResponse:
    if body.target_type == "product":
        if not body.target_id.startswith("prd_"):
            raise AppError(400, "VALIDATION_ERROR", "product 的 target_id 需要以 prd_ 开头")
        product = session.get(Product, body.target_id)
        if product is None:
            raise AppError(404, "NOT_FOUND", "产品不存在")
        full_name = None
        if product.github_repo_id:
            repo = session.get(GithubRepo, product.github_repo_id)
            if repo is not None:
                full_name = repo.full_name
        record = product_record(product, full_name)
    else:
        if not body.target_id.startswith("gh_"):
            raise AppError(400, "VALIDATION_ERROR", "github_repo 的 target_id 需要以 gh_ 开头")
        repo = session.get(GithubRepo, body.target_id)
        if repo is None:
            raise AppError(404, "NOT_FOUND", "仓库不存在")
        product_id = session.scalar(select(Product.id).where(Product.github_repo_id == repo.id))
        snapshot = latest_snapshot(session, repo.id, settings.zoneinfo)
        record = repo_record(
            repo,
            product_id=product_id,
            stars_total=None if snapshot is None else int(snapshot.stars),
            data_as_of=None if snapshot is None else snapshot.snapshot_date,
        )
    question = body.question.strip()
    if not question:
        raise AppError(400, "VALIDATION_ERROR", "question 不能为空")
    return answer_question(settings, record, question)


def _rankings(session: Session, settings: Settings, month: str | None):
    repos, snapshots = ranking_inputs(session, settings.zoneinfo)
    try:
        return resolve_rankings(
            today=today_in(settings.zoneinfo),
            repos=repos,
            snapshots=snapshots,
            tz=settings.zoneinfo,
            month=month,
        )
    except MonthNotAvailable as exc:
        raise AppError(400, "VALIDATION_ERROR", str(exc)) from exc
