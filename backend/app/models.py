"""Persistence models. Revenue is intentionally not a column."""

from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class GithubRepo(Base):
    __tablename__ = "github_repos"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    html_url: Mapped[str] = mapped_column(String(500), nullable=False)
    tagline_zh: Mapped[str | None] = mapped_column(String(300), nullable=True)


class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    tagline_zh: Mapped[str] = mapped_column(String(300), nullable=False)
    overview_zh: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    official_url: Mapped[str] = mapped_column(String(500), nullable=False)
    data_as_of: Mapped[date] = mapped_column(Date, nullable=False)
    pricing_value: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    pricing_unit: Mapped[str | None] = mapped_column(String(64), nullable=True)
    pricing_summary_zh: Mapped[str | None] = mapped_column(Text, nullable=True)
    pricing_source: Mapped[str | None] = mapped_column(String(500), nullable=True)
    metrics: Mapped[list] = mapped_column(JSON, nullable=False)
    github_repo_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("github_repos.id"), nullable=True
    )
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, index=True)


class StarSnapshot(Base):
    """One public star total for a repo on a calendar date in APP_TIMEZONE."""

    __tablename__ = "github_star_snapshots"
    __table_args__ = (UniqueConstraint("repo_id", "snapshot_date", name="uq_snapshot_repo_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    repo_id: Mapped[str] = mapped_column(String(64), ForeignKey("github_repos.id"), nullable=False, index=True)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    stars: Mapped[int] = mapped_column(Integer, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
