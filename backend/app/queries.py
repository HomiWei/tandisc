"""Read models into the shapes the ranking and ask services expect."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import GithubRepo, Product, StarSnapshot
from app.services.ranking import RepoInput, SnapshotPoint


def as_date(value: object) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _as_datetime(value: object, tz: ZoneInfo) -> datetime:
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    if not isinstance(value, datetime):
        raise TypeError("snapshot captured_at is not a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=tz)
    return value.astimezone(tz)


def ranking_inputs(session: Session, tz: ZoneInfo) -> tuple[list[RepoInput], list[SnapshotPoint]]:
    product_by_repo = {
        product.github_repo_id: product.id
        for product in session.scalars(select(Product).where(Product.github_repo_id.is_not(None)))
        if product.github_repo_id
    }
    repos = [
        RepoInput(
            id=repo.id,
            full_name=repo.full_name,
            html_url=repo.html_url,
            tagline_zh=repo.tagline_zh,
            product_id=product_by_repo.get(repo.id),
        )
        for repo in session.scalars(select(GithubRepo)).all()
    ]
    snapshots = [
        SnapshotPoint(
            repo_id=row.repo_id,
            snapshot_date=as_date(row.snapshot_date),
            stars=int(row.stars),
            captured_at=_as_datetime(row.captured_at, tz),
        )
        for row in session.scalars(select(StarSnapshot)).all()
    ]
    return repos, snapshots


def product_record(product: Product, github_full_name: str | None) -> dict:
    from app.serialize import metrics_from, pricing_from

    pricing = pricing_from(product)
    return {
        "id": product.id,
        "name": product.name,
        "tagline_zh": product.tagline_zh,
        "overview_zh": product.overview_zh,
        "category": product.category,
        "official_url": product.official_url,
        "data_as_of": product.data_as_of.isoformat(),
        "pricing": pricing.model_dump(),
        "metrics": [metric.model_dump() for metric in metrics_from(product.metrics)],
        "github_repo_id": product.github_repo_id,
        "github_full_name": github_full_name,
    }


def latest_snapshot(session: Session, repo_id: str, tz: ZoneInfo) -> StarSnapshot | None:
    rows = session.scalars(select(StarSnapshot).where(StarSnapshot.repo_id == repo_id)).all()
    if not rows:
        return None
    return max(rows, key=lambda row: _as_datetime(row.captured_at, tz))


def repo_record(
    repo: GithubRepo,
    *,
    product_id: str | None,
    stars_total: int | None,
    data_as_of: date | None,
) -> dict:
    return {
        "id": repo.id,
        "full_name": repo.full_name,
        "html_url": repo.html_url,
        "tagline_zh": repo.tagline_zh,
        "product_id": product_id,
        "stars_total": stars_total,
        "data_as_of": None if data_as_of is None else data_as_of.isoformat(),
    }
