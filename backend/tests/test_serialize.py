"""Source objects are wrapped from stored URLs and omitted when the URL is missing."""

import json
from datetime import date

from app.models import Product
from app.queries import product_record
from app.serialize import metrics_from, pricing_from, usable_http_url


def _product(**overrides) -> Product:
    fields = {
        "id": "prd_example",
        "name": "Example",
        "tagline_zh": "一句话",
        "overview_zh": "概述",
        "category": "other",
        "official_url": "https://example.com",
        "data_as_of": date(2026, 11, 16),
        "pricing_value": None,
        "pricing_unit": None,
        "pricing_summary_zh": "见官网",
        "pricing_source": "https://example.com/pricing",
        "metrics": [],
        "github_repo_id": None,
        "display_order": 1,
    }
    fields.update(overrides)
    return Product(**fields)


def test_usable_http_url_rejects_non_links():
    assert usable_http_url("https://example.com/pricing") == "https://example.com/pricing"
    assert usable_http_url("  https://example.com/pricing  ") == "https://example.com/pricing"
    for raw in (
        None,
        "",
        "   ",
        "官网定价页",
        "example.com/pricing",
        "javascript:alert(1)",
        "ftp://example.com/pricing",
        "https://",
        "https:///pricing",
        "http://",
        12,
        {"url": "https://example.com/pricing"},
    ):
        assert usable_http_url(raw) is None


def test_pricing_source_present_uses_stored_url_and_data_as_of():
    pricing = pricing_from(_product(pricing_value=8, pricing_unit="USD")).model_dump(mode="json")
    assert pricing["value"] == 8
    assert pricing["unit"] == "USD"
    assert pricing["summary_zh"] == "见官网"
    assert pricing["source"] == {
        "name": "官网定价页",
        "url": "https://example.com/pricing",
        "accessed_at": "2026-11-16",
    }


def test_pricing_source_null_when_url_missing_or_unusable():
    missing = pricing_from(
        _product(pricing_value=8, pricing_unit="USD", pricing_source=None)
    ).model_dump(mode="json")
    assert missing["value"] is None
    assert missing["unit"] is None
    assert missing["source"] is None
    assert missing["summary_zh"] == "见官网"

    blank = pricing_from(
        _product(pricing_value=0, pricing_unit="USD", pricing_source="not-a-url")
    ).model_dump(mode="json")
    assert blank["value"] is None
    assert blank["unit"] is None
    assert blank["source"] is None


def test_product_record_embeds_source_object_as_json():
    record = product_record(_product(), None)
    encoded = json.dumps(record, ensure_ascii=False)
    assert record["pricing"]["source"] == {
        "name": "官网定价页",
        "url": "https://example.com/pricing",
        "accessed_at": "2026-11-16",
    }
    assert '"source": "https://' not in encoded
    assert "2026-11-16" in encoded


def test_metric_source_object_and_null_cases():
    metrics = metrics_from(
        [
            {
                "key": "priced",
                "label_zh": "有来源",
                "value": 2,
                "unit": "个",
                "source": {"name": "公开文档", "url": "https://example.com/docs", "accessed_at": "2026-09-01"},
            },
            {"key": "bare", "label_zh": "只有链接", "value": 1, "unit": "个", "source": "https://example.com/a"},
            {"key": "none", "label_zh": "无来源", "value": 9, "unit": "个"},
            {"key": "bad", "label_zh": "坏链接", "value": 4, "unit": "个", "source": "see docs"},
            "skip",
            {"label_zh": "缺 key", "value": 1, "source": "https://example.com/a"},
        ],
        data_as_of=date(2026, 11, 16),
    )
    dumped = [item.model_dump(mode="json") for item in metrics]
    assert dumped[0]["source"] == {
        "name": "公开文档",
        "url": "https://example.com/docs",
        "accessed_at": "2026-09-01",
    }
    assert dumped[0]["value"] == 2
    assert dumped[1]["source"] == {
        "name": None,
        "url": "https://example.com/a",
        "accessed_at": "2026-11-16",
    }
    assert dumped[2]["value"] is None
    assert dumped[2]["source"] is None
    assert dumped[3]["value"] is None
    assert dumped[3]["unit"] is None
    assert dumped[3]["source"] is None
    assert [item["key"] for item in dumped] == ["priced", "bare", "none", "bad"]
