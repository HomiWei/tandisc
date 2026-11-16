"""Initial products, github repos, and star snapshots.

Revision ID: 20261116_0001
Revises:
Create Date: 2026-11-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20261116_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "github_repos",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("html_url", sa.String(length=500), nullable=False),
        sa.Column("tagline_zh", sa.String(length=300), nullable=True),
        sa.UniqueConstraint("full_name"),
    )
    op.create_table(
        "products",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("tagline_zh", sa.String(length=300), nullable=False),
        sa.Column("overview_zh", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("official_url", sa.String(length=500), nullable=False),
        sa.Column("data_as_of", sa.Date(), nullable=False),
        sa.Column("pricing_value", sa.Numeric(18, 4), nullable=True),
        sa.Column("pricing_unit", sa.String(length=64), nullable=True),
        sa.Column("pricing_summary_zh", sa.Text(), nullable=True),
        sa.Column("pricing_source", sa.String(length=500), nullable=True),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("github_repo_id", sa.String(length=64), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["github_repo_id"], ["github_repos.id"]),
    )
    op.create_index("ix_products_name", "products", ["name"])
    op.create_index("ix_products_category", "products", ["category"])
    op.create_index("ix_products_display_order", "products", ["display_order"])
    op.create_table(
        "github_star_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("repo_id", sa.String(length=64), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("stars", sa.Integer(), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["repo_id"], ["github_repos.id"]),
        sa.UniqueConstraint("repo_id", "snapshot_date", name="uq_snapshot_repo_date"),
    )
    op.create_index("ix_github_star_snapshots_repo_id", "github_star_snapshots", ["repo_id"])
    op.create_index("ix_github_star_snapshots_snapshot_date", "github_star_snapshots", ["snapshot_date"])


def downgrade() -> None:
    op.drop_index("ix_github_star_snapshots_snapshot_date", table_name="github_star_snapshots")
    op.drop_index("ix_github_star_snapshots_repo_id", table_name="github_star_snapshots")
    op.drop_table("github_star_snapshots")
    op.drop_index("ix_products_display_order", table_name="products")
    op.drop_index("ix_products_category", table_name="products")
    op.drop_index("ix_products_name", table_name="products")
    op.drop_table("products")
    op.drop_table("github_repos")
