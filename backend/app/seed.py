"""Load the curated catalog. Startup inserts missing ids; the CLI can refresh text."""

import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.catalog import PRODUCTS, URLS_VERIFIED_ON
from app.config import get_settings
from app.db import Base, make_engine, make_session_factory
from app.logging_config import configure_logging
from app.models import Product

logger = logging.getLogger("tandisc.seed")


def _insert(row: dict) -> Product:
    return Product(
        id=row["id"],
        name=row["name"],
        tagline_zh=row["tagline_zh"],
        overview_zh=row["overview_zh"],
        category=row["category"],
        official_url=row["official_url"],
        data_as_of=URLS_VERIFIED_ON,
        pricing_value=None,
        pricing_unit=None,
        pricing_summary_zh=row["pricing_summary_zh"],
        pricing_source=row["pricing_source"],
        metrics=[],
        github_repo_id=None,
        display_order=row["display_order"],
    )


def _refresh_text(product: Product, row: dict) -> None:
    product.name = row["name"]
    product.tagline_zh = row["tagline_zh"]
    product.overview_zh = row["overview_zh"]
    product.category = row["category"]
    product.official_url = row["official_url"]
    product.data_as_of = URLS_VERIFIED_ON
    product.pricing_summary_zh = row["pricing_summary_zh"]
    product.pricing_source = row["pricing_source"]
    product.display_order = row["display_order"]


def seed_products(session: Session, *, update_existing: bool = False) -> int:
    """Insert catalog rows that are missing. Optionally refresh descriptive fields.

    Existing github_repo_id, metrics, and pricing numbers are left in place so a
    re-seed does not unlink a repo or wipe a value that was added later.
    """
    changed = 0
    for row in PRODUCTS:
        current = session.get(Product, row["id"])
        if current is None:
            session.add(_insert(row))
            changed += 1
        elif update_existing:
            _refresh_text(current, row)
            changed += 1
    session.commit()
    return changed


def main() -> int:
    configure_logging()
    settings = get_settings()
    engine = make_engine(settings.sqlalchemy_url)
    Base.metadata.create_all(bind=engine)
    session_factory = make_session_factory(engine)
    with session_factory() as session:
        changed = seed_products(session, update_existing=True)
        total = session.scalar(select(func.count()).select_from(Product))
    logger.info("seed complete changed=%s total=%s dialect=%s", changed, total, engine.dialect.name)
    print(f"seed complete changed={changed} total={total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
