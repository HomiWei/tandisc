import json
import logging

from app.domain import INSUFFICIENT_ANSWER, OUT_OF_SCOPE_ANSWER
from app.errors import AppError
from app.logging_config import JsonFormatter, redact
from app.services.ask import guard_model_payload, local_decision
from app.services.snapshots import run_daily_snapshot


def test_local_rules_do_not_invent_numbers():
    record = {
        "name": "Linear",
        "overview_zh": "用来登记需求",
        "pricing": {"value": None, "unit": None, "summary_zh": "见官网", "source": "https://linear.app/pricing"},
        "stars_total": None,
    }
    revenue = local_decision("这家公司营收是多少？", record)
    assert revenue is not None
    assert revenue.status == "insufficient_data"
    assert revenue.answer == INSUFFICIENT_ANSWER

    price = local_decision("月费是多少钱？", record)
    assert price is not None
    assert price.status == "insufficient_data"

    advice = local_decision("我应该买入这家公司的股票吗？", record)
    assert advice is not None
    assert advice.status == "out_of_scope"
    assert advice.answer == OUT_OF_SCOPE_ANSWER

    assert local_decision("这个产品是做什么的？", record) is None


def test_model_answer_with_an_invented_number_is_rejected():
    record = {"name": "Linear", "overview_zh": "用来登记需求", "pricing": {"value": None}}
    guarded = guard_model_payload(
        {
            "answer": "月费是 8 美元",
            "status": "answered",
            "citations": [{"field": "pricing", "source": "https://linear.app/pricing"}],
        },
        record,
    )
    assert guarded.status == "insufficient_data"
    assert guarded.answer == INSUFFICIENT_ANSWER


def test_model_answer_with_an_unknown_url_is_rejected():
    record = {"name": "Linear", "official_url": "https://linear.app"}
    guarded = guard_model_payload(
        {"answer": "官网是 https://evil.example/linear", "status": "answered", "citations": []},
        record,
    )
    assert guarded.status == "insufficient_data"
    assert guarded.answer == INSUFFICIENT_ANSWER


def test_model_answer_can_quote_stored_text():
    record = {"name": "Linear", "overview_zh": "用来登记需求", "official_url": "https://linear.app"}
    guarded = guard_model_payload(
        {
            "answer": "Linear 用来登记需求",
            "status": "answered",
            "citations": [{"field": "overview_zh", "source": None}, {"field": "not_a_field", "source": None}],
        },
        record,
    )
    assert guarded.status == "answered"
    assert guarded.answer == "Linear 用来登记需求"
    assert [item.field for item in guarded.citations] == ["overview_zh"]


def test_out_of_scope_model_text_is_replaced():
    guarded = guard_model_payload(
        {"answer": "建议立刻买入", "status": "out_of_scope", "citations": []},
        {"name": "Linear"},
    )
    assert guarded.answer == OUT_OF_SCOPE_ANSWER
    assert "买入" not in guarded.answer


def test_upstream_error_does_not_echo_the_secret(monkeypatch):
    from app.config import Settings
    from app.services.ask import call_llm

    class _Response:
        status_code = 401

        def json(self):
            return {"error": "super-secret-token"}

    class _Client:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, url, json, headers):
            assert "super-secret-token" not in url
            return _Response()

    monkeypatch.setattr("app.services.ask.httpx.Client", _Client)
    settings = Settings(
        _env_file=None,
        llm_base_url="https://llm.example.test/v1",
        llm_api_key="super-secret-token",
        llm_model="demo",
    )
    try:
        call_llm(settings, {"name": "Linear"}, "这个产品是做什么的？")
    except AppError as exc:
        assert exc.status_code == 503
        assert exc.code == "UPSTREAM_UNAVAILABLE"
        assert "super-secret-token" not in exc.message
    else:
        raise AssertionError("expected upstream error")


def test_snapshot_stub_does_not_echo_a_token_or_call_github():
    skipped = run_daily_snapshot(None)
    assert skipped["status"] == "skipped"
    pending = run_daily_snapshot("ghp_should_not_echo")
    assert pending["status"] == "not_implemented"
    assert "ghp_should_not_echo" not in json.dumps(pending)


def test_log_formatter_redacts_secrets():
    hidden = redact("Authorization=Bearer super-secret-token token=ghp_abc")
    assert "super-secret-token" not in hidden
    assert "ghp_abc" not in hidden
    record = logging.LogRecord("tandisc", logging.INFO, __file__, 1, hidden, None, None)
    payload = json.loads(JsonFormatter().format(record))
    assert payload["level"] == "INFO"
    assert "super-secret-token" not in payload["message"]
