import json
from datetime import datetime
from zoneinfo import ZoneInfo

from app.catalog import URLS_VERIFIED_ON
from app.domain import CATEGORIES, INSUFFICIENT_ANSWER, METHODOLOGY_ZH
from app.models import GithubRepo, Product, StarSnapshot
from app.seed import seed_products

LIST_KEYS = {"id", "name", "tagline_zh", "category", "official_url", "github_repo_id"}
DETAIL_KEYS = LIST_KEYS | {"overview_zh", "data_as_of", "pricing", "metrics", "github_full_name"}
PERIOD_KEYS = {
    "year_month",
    "timezone",
    "label_zh",
    "is_fallback_previous_month",
    "fallback_reason",
    "data_as_of",
    "start_date",
    "end_date",
    "methodology_zh",
    "empty_reason_zh",
    "note_zh",
}
RANK_KEYS = {
    "rank",
    "repo_id",
    "full_name",
    "html_url",
    "tagline_zh",
    "stars_start",
    "stars_end",
    "net_gain",
    "stars_total",
    "product_id",
}
TZ = ZoneInfo("Asia/Shanghai")


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "charset=utf-8" in response.headers["content-type"].lower()
    cors = client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert cors.headers["access-control-allow-origin"] == "*"


def test_products_seed_count_shape_and_filters(client):
    response = client.get("/api/v1/products")
    assert response.status_code == 200
    body = response.json()
    assert body["page"] == 1
    assert body["page_size"] == 30
    assert body["total"] >= 30
    assert len(body["items"]) == 30
    assert body["items"][0]["id"] == "prd_linear"
    assert body["items"][0]["name"] == "Linear"
    raw = response.content.decode("utf-8")
    assert "给软件团队用的议题跟踪工具" in raw
    for item in body["items"]:
        assert set(item) == LIST_KEYS
        assert item["category"] in CATEGORIES
        assert item["official_url"].startswith("https://")
        assert item["github_repo_id"] is None
    blob = json.dumps(body)
    for forbidden in ("revenue", "pricing", "metrics", "overview_zh"):
        assert forbidden not in blob

    wider = client.get("/api/v1/products", params={"page_size": 50})
    assert wider.json()["total"] == body["total"]
    assert len(wider.json()["items"]) == body["total"]

    second = client.get("/api/v1/products", params={"page": 2})
    assert second.json()["items"] == []
    assert second.json()["total"] == body["total"]

    by_name = client.get("/api/v1/products", params={"sort": "name", "page_size": 50})
    assert by_name.json()["items"][0]["name"] == "Airtable"

    found = client.get("/api/v1/products", params={"q": "FIG"})
    assert [item["name"] for item in found.json()["items"]] == ["Figma"]

    wildcard = client.get("/api/v1/products", params={"q": "%"})
    assert wildcard.json()["total"] == 0

    ai = client.get("/api/v1/products", params={"category": "ai", "page_size": 50})
    assert ai.json()["total"] == 3
    assert {item["id"] for item in ai.json()["items"]} == {
        "prd_huggingface",
        "prd_replicate",
        "prd_pinecone",
    }

    invalid = client.get("/api/v1/products", params={"category": "skincare"})
    assert invalid.status_code == 400
    assert invalid.json()["error"]["code"] == "VALIDATION_ERROR"

    too_big = client.get("/api/v1/products", params={"page_size": 51})
    assert too_big.status_code == 400
    assert too_big.json()["error"]["code"] == "VALIDATION_ERROR"


def test_product_detail_and_missing(client):
    response = client.get("/api/v1/products/prd_linear")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == DETAIL_KEYS
    assert body["data_as_of"] == URLS_VERIFIED_ON.isoformat()
    assert body["pricing"]["value"] is None
    assert body["pricing"]["unit"] is None
    assert body["pricing"]["source"] == {
        "name": "官网定价页",
        "url": "https://linear.app/pricing",
        "accessed_at": URLS_VERIFIED_ON.isoformat(),
    }
    assert isinstance(body["pricing"]["source"], dict)
    assert body["pricing"]["summary_zh"]
    assert body["metrics"] == []
    assert body["github_full_name"] is None
    assert "revenue" not in body
    encoded = response.content.decode("utf-8")
    assert "\\u" not in encoded

    missing = client.get("/api/v1/products/prd_missing")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "NOT_FOUND"


def test_monthly_rankings_empty_period_and_meta(client):
    response = client.get("/api/v1/github/monthly-rankings")
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["page"] == 1
    assert body["page_size"] == 50
    assert body["total"] == 0
    period = body["period"]
    assert set(period) == PERIOD_KEYS
    assert period["year_month"] == "2026-11"
    assert period["is_fallback_previous_month"] is False
    assert period["fallback_reason"] is None
    assert period["label_zh"] == "本月至今"
    assert period["methodology_zh"] == METHODOLOGY_ZH
    assert period["data_as_of"] is None
    assert period["start_date"] == "2026-11-01"
    assert period["end_date"] == "2026-11-16"
    assert period["empty_reason_zh"]
    assert period["timezone"] == "Asia/Shanghai"
    assert "revenue" not in response.content.decode("utf-8")

    meta = client.get("/api/v1/meta")
    assert meta.status_code == 200
    meta_body = meta.json()
    assert set(meta_body) == {"categories", "github_period"}
    assert "github_ranking_period" not in meta_body
    assert meta_body["categories"] == CATEGORIES
    meta_period = meta_body["github_period"]
    assert meta_period == period
    assert set(meta_period) == PERIOD_KEYS
    assert meta_period["year_month"] == "2026-11"
    assert meta_period["label_zh"] == "本月至今"
    assert meta_period["is_fallback_previous_month"] is False
    assert meta_period["fallback_reason"] is None

    future = client.get("/api/v1/github/monthly-rankings", params={"month": "2026-13"})
    assert future.status_code == 400
    assert future.json()["error"]["code"] == "VALIDATION_ERROR"

    missing_repo = client.get("/api/v1/github/repos/gh_missing")
    assert missing_repo.status_code == 404
    assert missing_repo.json()["error"]["code"] == "NOT_FOUND"


def test_monthly_rankings_days_1_to_7_use_previous_month(client, monkeypatch):
    monkeypatch.setattr(
        "app.services.clock.now",
        lambda tz: datetime(2026, 11, 7, 12, 0, tzinfo=TZ),
    )
    body = client.get("/api/v1/github/monthly-rankings").json()
    assert body["items"] == []
    period = body["period"]
    assert period["year_month"] == "2026-10"
    assert period["start_date"] == "2026-10-01"
    assert period["end_date"] == "2026-10-31"
    assert period["label_zh"] == "上一完整月"
    assert period["is_fallback_previous_month"] is True
    assert period["fallback_reason"] == "current_month_snapshots_incomplete"


def test_rankings_roundtrip_snapshots_without_inventing_gain(client):
    factory = client.app.state.session_factory
    with factory() as session:
        session.add(
            GithubRepo(
                id="gh_demo",
                full_name="acme/demo",
                html_url="https://github.com/acme/demo",
                tagline_zh="示例仓库",
            )
        )
        session.add(
            StarSnapshot(
                repo_id="gh_demo",
                snapshot_date=datetime(2026, 11, 1).date(),
                stars=100,
                captured_at=datetime(2026, 11, 1, 8, 0, tzinfo=TZ),
            )
        )
        session.add(
            StarSnapshot(
                repo_id="gh_demo",
                snapshot_date=datetime(2026, 11, 16).date(),
                stars=140,
                captured_at=datetime(2026, 11, 16, 9, 0, tzinfo=TZ),
            )
        )
        product = session.get(Product, "prd_linear")
        product.github_repo_id = "gh_demo"
        session.commit()

    rankings = client.get("/api/v1/github/monthly-rankings").json()
    assert rankings["period"]["year_month"] == "2026-11"
    assert rankings["period"]["is_fallback_previous_month"] is False
    assert rankings["period"]["fallback_reason"] is None
    assert rankings["period"]["data_as_of"] == "2026-11-16"
    assert rankings["total"] == 1
    item = rankings["items"][0]
    assert set(item) == RANK_KEYS
    assert item["rank"] == 1
    assert item["stars_start"] == 100
    assert item["stars_end"] == 140
    assert item["net_gain"] == 40
    assert item["stars_total"] == 140
    assert item["product_id"] == "prd_linear"
    assert "revenue" not in item

    detail = client.get("/api/v1/products/prd_linear").json()
    assert detail["github_repo_id"] == "gh_demo"
    assert detail["github_full_name"] == "acme/demo"
    listed = client.get("/api/v1/products", params={"q": "Linear"}).json()["items"][0]
    assert set(listed) == LIST_KEYS
    assert "pricing" not in listed

    repo = client.get("/api/v1/github/repos/gh_demo")
    assert repo.status_code == 200
    repo_body = repo.json()
    assert repo_body["stars_total"] == 140
    assert repo_body["data_as_of"] == "2026-11-16"
    assert repo_body["product_id"] == "prd_linear"
    assert "revenue" not in repo_body


def test_ask_without_llm(client):
    missing_data = client.post(
        "/api/v1/ask",
        json={"target_type": "product", "target_id": "prd_linear", "question": "这家公司营收是多少？"},
    )
    assert missing_data.status_code == 200
    assert missing_data.json() == {
        "answer": INSUFFICIENT_ANSWER,
        "status": "insufficient_data",
        "citations": [],
    }

    out_of_scope = client.post(
        "/api/v1/ask",
        json={"target_type": "product", "target_id": "prd_stripe", "question": "我应该买入这家公司的股票吗？"},
    )
    assert out_of_scope.status_code == 200
    assert out_of_scope.json()["status"] == "out_of_scope"

    unavailable = client.post(
        "/api/v1/ask",
        json={"target_type": "product", "target_id": "prd_linear", "question": "这个产品是做什么的？"},
    )
    assert unavailable.status_code == 503
    assert unavailable.json()["error"]["code"] == "UPSTREAM_UNAVAILABLE"
    assert "super-secret" not in unavailable.text

    missing = client.post(
        "/api/v1/ask",
        json={"target_type": "product", "target_id": "prd_missing", "question": "介绍一下"},
    )
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "NOT_FOUND"

    bad_prefix = client.post(
        "/api/v1/ask",
        json={"target_type": "product", "target_id": "gh_demo", "question": "介绍一下"},
    )
    assert bad_prefix.status_code == 400
    assert bad_prefix.json()["error"]["code"] == "VALIDATION_ERROR"

    invalid = client.post("/api/v1/ask", json={})
    assert invalid.status_code == 400
    assert invalid.json()["error"]["code"] == "VALIDATION_ERROR"

    missing_repo = client.post(
        "/api/v1/ask",
        json={"target_type": "github_repo", "target_id": "gh_missing", "question": "star 是多少？"},
    )
    assert missing_repo.status_code == 404


def test_detail_source_object_present_and_null(client):
    factory = client.app.state.session_factory
    with factory() as session:
        kept = session.get(Product, "prd_notion")
        kept.pricing_value = 10
        kept.pricing_unit = "USD"
        kept.pricing_source = " https://www.notion.so/pricing "
        kept.data_as_of = datetime(2026, 11, 2).date()
        kept.metrics = [
            {
                "key": "seats",
                "label_zh": "席位",
                "value": 3,
                "unit": "个",
                "source": "https://www.notion.so/pricing",
            },
            {
                "key": "mau",
                "label_zh": "月活",
                "value": 100,
                "unit": "人",
                "source": "未公开",
            },
            {
                "key": "editors",
                "label_zh": "编辑者",
                "value": 5,
                "unit": "人",
                "source_name": "公开说明",
                "source_url": "https://www.notion.so/pricing",
                "accessed_at": "2026-10-01",
            },
        ]
        missing = session.get(Product, "prd_figma")
        missing.pricing_value = 12
        missing.pricing_unit = "USD"
        missing.pricing_source = None
        missing.pricing_summary_zh = "价格说明仍保留，但没有可链接的来源。"
        missing.metrics = [
            {"key": "seats", "label_zh": "席位", "value": 8, "unit": "个", "source": None},
            {"key": "blank", "label_zh": "空来源", "value": 1, "unit": "个", "source": "   "},
            {"key": "scheme", "label_zh": "无协议", "value": 2, "unit": "个", "source": "www.figma.com/pricing"},
        ]
        unusable = session.get(Product, "prd_slack")
        unusable.pricing_value = 0
        unusable.pricing_unit = "USD"
        unusable.pricing_source = "ftp://slack.com/pricing"
        unusable.metrics = [
            {
                "key": "plans",
                "label_zh": "方案",
                "value": 4,
                "unit": "档",
                "source": {"name": "官网定价页", "url": "not a url", "accessed_at": "2026-11-01"},
            }
        ]
        session.commit()

    notion = client.get("/api/v1/products/prd_notion").json()
    assert notion["pricing"]["value"] == 10
    assert notion["pricing"]["unit"] == "USD"
    assert notion["pricing"]["source"] == {
        "name": "官网定价页",
        "url": "https://www.notion.so/pricing",
        "accessed_at": "2026-11-02",
    }
    assert notion["metrics"][0] == {
        "key": "seats",
        "label_zh": "席位",
        "value": 3.0,
        "unit": "个",
        "source": {
            "name": None,
            "url": "https://www.notion.so/pricing",
            "accessed_at": "2026-11-02",
        },
    }
    assert notion["metrics"][1]["value"] is None
    assert notion["metrics"][1]["unit"] is None
    assert notion["metrics"][1]["source"] is None
    assert notion["metrics"][2]["value"] == 5
    assert notion["metrics"][2]["source"] == {
        "name": "公开说明",
        "url": "https://www.notion.so/pricing",
        "accessed_at": "2026-10-01",
    }
    encoded = client.get("/api/v1/products/prd_notion").content.decode("utf-8")
    assert '"source":"https://' not in encoded
    assert '"source":"http://' not in encoded

    figma = client.get("/api/v1/products/prd_figma").json()
    assert figma["pricing"]["value"] is None
    assert figma["pricing"]["unit"] is None
    assert figma["pricing"]["source"] is None
    assert figma["pricing"]["summary_zh"] == "价格说明仍保留，但没有可链接的来源。"
    assert [item["source"] for item in figma["metrics"]] == [None, None, None]
    assert [item["value"] for item in figma["metrics"]] == [None, None, None]

    slack = client.get("/api/v1/products/prd_slack").json()
    assert slack["pricing"]["value"] is None
    assert slack["pricing"]["source"] is None
    assert slack["metrics"][0]["value"] is None
    assert slack["metrics"][0]["source"] is None


def test_seed_is_idempotent(client):
    factory = client.app.state.session_factory
    with factory() as session:
        assert seed_products(session, update_existing=False) == 0
    assert client.get("/api/v1/products", params={"page_size": 50}).json()["total"] == 30
