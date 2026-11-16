"""Map database rows onto the public response models."""

import math
from datetime import date, datetime
from urllib.parse import urlsplit

from app.models import Product
from app.schemas import Metric, Pricing, ProductDetail, ProductListItem, Source

# Stored pricing rows keep a URL only. The public name is a label for that page, not a new fact.
OFFICIAL_PRICING_SOURCE_NAME = "官网定价页"


def usable_http_url(value: object) -> str | None:
    """Return a stored http(s) URL, or None when the value cannot be linked."""
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    if not candidate or any(char.isspace() for char in candidate):
        return None
    parts = urlsplit(candidate)
    if parts.scheme.lower() not in {"http", "https"}:
        return None
    if not parts.hostname:
        return None
    return candidate


def _as_date(value: object) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        return None
    text = value.strip()
    if len(text) > 10 and text[10] in "T ":
        text = text[:10]
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _clean_name(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _as_float(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def source_from_url(url: object, *, name: str | None, accessed_at: object) -> Source | None:
    usable = usable_http_url(url)
    if usable is None:
        return None
    return Source(name=_clean_name(name), url=usable, accessed_at=_as_date(accessed_at))


def _metric_source(item: dict, data_as_of: object) -> Source | None:
    """Read a stored metric source without inventing a URL or a date."""
    fallback_date = _as_date(item.get("accessed_at")) or _as_date(data_as_of)
    stored_name = _clean_name(item.get("source_name"))
    raw = item.get("source")
    if isinstance(raw, dict):
        url = usable_http_url(raw.get("url")) or usable_http_url(item.get("source_url"))
        if url is None:
            return None
        name = _clean_name(raw.get("name")) or stored_name
        when = _as_date(raw.get("accessed_at")) or fallback_date
        return Source(name=name, url=url, accessed_at=when)
    url = usable_http_url(raw) or usable_http_url(item.get("source_url"))
    if url is None:
        return None
    return Source(name=stored_name, url=url, accessed_at=fallback_date)


def pricing_from(product: Product) -> Pricing:
    source = source_from_url(
        product.pricing_source,
        name=OFFICIAL_PRICING_SOURCE_NAME,
        accessed_at=product.data_as_of,
    )
    value = _as_float(product.pricing_value)
    unit = product.pricing_unit
    # A number with no usable source is not reliable and must not be shown.
    if source is None:
        value = None
        unit = None
    elif value is None:
        unit = None
    return Pricing(
        value=value,
        unit=unit,
        summary_zh=product.pricing_summary_zh,
        source=source,
    )


def metrics_from(raw: object, *, data_as_of: date | None = None) -> list[Metric]:
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
        source = _metric_source(item, data_as_of)
        value = _as_float(item.get("value")) if source is not None else None
        unit = item.get("unit")
        if value is None:
            unit = None
        metrics.append(
            Metric(
                key=str(key),
                label_zh=str(label),
                value=value,
                unit=None if unit in (None, "") else str(unit),
                source=source,
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
        metrics=metrics_from(product.metrics, data_as_of=product.data_as_of),
        github_repo_id=product.github_repo_id,
        github_full_name=github_full_name,
    )
