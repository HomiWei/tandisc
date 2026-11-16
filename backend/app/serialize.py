"""Map database rows onto the public response models."""

from app.models import Product
from app.schemas import Metric, Pricing, ProductDetail, ProductListItem


def pricing_from(product: Product) -> Pricing:
    source = product.pricing_source or None
    value = None if product.pricing_value is None else float(product.pricing_value)
    unit = product.pricing_unit
    # A number with no source is not reliable and must not be shown.
    if value is not None and not source:
        value = None
        unit = None
    if value is None:
        unit = None
    return Pricing(
        value=value,
        unit=unit,
        summary_zh=product.pricing_summary_zh,
        source=source,
    )


def metrics_from(raw: object) -> list[Metric]:
    if not isinstance(raw, list):
        return []
    metrics: list[Metric] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        key = item.get("key")
        label = item.get("label_zh")
        if not key or not label:
            continue
        source = item.get("source") or None
        value = item.get("value")
        unit = item.get("unit")
        if value is not None and not source:
            value = None
            unit = None
        if value is not None:
            try:
                value = float(value)
            except (TypeError, ValueError):
                value = None
                unit = None
        metrics.append(
            Metric(
                key=str(key),
                label_zh=str(label),
                value=value,
                unit=None if unit in (None, "") else str(unit),
                source=None if source in (None, "") else str(source),
            )
        )
    return metrics


def product_list_item(product: Product) -> ProductListItem:
    return ProductListItem(
        id=product.id,
        name=product.name,
        tagline_zh=product.tagline_zh,
        category=product.category,
        official_url=product.official_url,
        github_repo_id=product.github_repo_id,
    )


def product_detail(product: Product, github_full_name: str | None) -> ProductDetail:
    return ProductDetail(
        id=product.id,
        name=product.name,
        tagline_zh=product.tagline_zh,
        overview_zh=product.overview_zh,
        category=product.category,
        official_url=product.official_url,
        data_as_of=product.data_as_of,
        pricing=pricing_from(product),
        metrics=metrics_from(product.metrics),
        github_repo_id=product.github_repo_id,
        github_full_name=github_full_name,
    )
