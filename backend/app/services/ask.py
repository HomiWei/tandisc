"""Grounded Q&A over one stored record.

Out-of-scope and missing-data questions are answered locally. Anything that
needs a sentence composed from the record goes to the configured LLM. Numeric
claims that are not present in the record are dropped.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx

from app.config import Settings
from app.domain import INSUFFICIENT_ANSWER, OUT_OF_SCOPE_ANSWER
from app.errors import AppError
from app.schemas import AskResponse, Citation

logger = logging.getLogger("tandisc.ask")

_OUT_OF_SCOPE = re.compile(
    r"投资|股票|股价|证券|诊断|处方|用药|症状|就医|医疗|"
    r"investment|\bstocks?\b|diagnos|prescription",
    re.IGNORECASE,
)
_MISSING_METRIC = re.compile(
    r"营收|收入|利润|估值|融资|用户数|用户量|月活|日活|流量|市场份额|"
    r"\bARR\b|\bMRR\b|\brevenue\b|\bvaluation\b|\bfunding\b|\bDAU\b|\bMAU\b",
    re.IGNORECASE,
)
_NUMERIC_PRICE = re.compile(
    r"多少钱|价格是多少|具体价格|月费|年费|how much|what does it cost",
    re.IGNORECASE,
)
_STARS = re.compile(r"\bstars?\b|标星|星星数", re.IGNORECASE)
_NUMBER = re.compile(r"\d+(?:\.\d+)?")
_URL = re.compile(r"https?://[^\s)）]+")

_SYSTEM_PROMPT = (
    "你是探盘的档案问答助手。只能根据用户消息里的 JSON 档案回答，不得使用档案以外的知识。\n"
    "规则：\n"
    "1. 不得编造任何数字、价格、收入、用户量、流量或排名。档案里没有的数字不要出现。\n"
    "2. 档案没有该信息时，answer 必须正好是「当前档案没有这项数据」，status 为 insufficient_data。\n"
    "3. 投资建议、买卖股票、医疗诊断、用药建议，status 为 out_of_scope，不要给出建议。\n"
    "4. 能根据档案原文回答时，status 为 answered。citations 列出用到的字段名；没有链接则 source 为 null。\n"
    "5. 只输出一个 JSON 对象："
    '{"answer":"","status":"answered|insufficient_data|out_of_scope","citations":[{"field":"","source":null}]}'
)


def _numbers(text: str) -> set[str]:
    return set(_NUMBER.findall(text))


def _pricing_value(record: dict[str, Any]) -> Any:
    pricing = record.get("pricing")
    if isinstance(pricing, dict):
        return pricing.get("value")
    return None


def local_decision(question: str, record: dict[str, Any]) -> AskResponse | None:
    """Return a final response when no model call is required."""
    if _OUT_OF_SCOPE.search(question):
        return AskResponse(answer=OUT_OF_SCOPE_ANSWER, status="out_of_scope", citations=[])
    if _MISSING_METRIC.search(question):
        return AskResponse(answer=INSUFFICIENT_ANSWER, status="insufficient_data", citations=[])
    if _NUMERIC_PRICE.search(question) and _pricing_value(record) is None:
        return AskResponse(answer=INSUFFICIENT_ANSWER, status="insufficient_data", citations=[])
    if _STARS.search(question) and record.get("stars_total") is None:
        return AskResponse(answer=INSUFFICIENT_ANSWER, status="insufficient_data", citations=[])
    return None


def guard_model_payload(payload: dict[str, Any], record: dict[str, Any]) -> AskResponse:
    status = payload.get("status")
    if status == "out_of_scope":
        return AskResponse(answer=OUT_OF_SCOPE_ANSWER, status="out_of_scope", citations=[])
    if status == "insufficient_data":
        return AskResponse(answer=INSUFFICIENT_ANSWER, status="insufficient_data", citations=[])
    if status != "answered":
        raise AppError(503, "UPSTREAM_UNAVAILABLE", "语言模型返回无法使用")

    record_text = json.dumps(record, ensure_ascii=False)
    answer = str(payload.get("answer") or "").strip()
    if not answer or not _numbers(answer).issubset(_numbers(record_text)):
        return AskResponse(answer=INSUFFICIENT_ANSWER, status="insufficient_data", citations=[])
    if not set(_URL.findall(answer)).issubset(_URL.findall(record_text)):
        return AskResponse(answer=INSUFFICIENT_ANSWER, status="insufficient_data", citations=[])

    known_fields = set(record.keys())
    known_sources = set(_URL.findall(record_text))
    citations: list[Citation] = []
    raw_citations = payload.get("citations") or []
    if isinstance(raw_citations, list):
        for item in raw_citations:
            if not isinstance(item, dict):
                continue
            field = str(item.get("field") or "")
            if field not in known_fields:
                continue
            source = item.get("source")
            if source in (None, ""):
                citations.append(Citation(field=field, source=None))
            elif str(source) in known_sources:
                citations.append(Citation(field=field, source=str(source)))
    return AskResponse(answer=answer, status="answered", citations=citations)


def _parse_model_json(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no json object")
    parsed = json.loads(text[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("json is not an object")
    return parsed


def _llm_url(base_url: str) -> str:
    base = base_url.strip().rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    return base + "/chat/completions"


def call_llm(settings: Settings, record: dict[str, Any], question: str) -> AskResponse:
    payload = {
        "model": settings.llm_model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps({"record": record, "question": question}, ensure_ascii=False),
            },
        ],
    }
    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.post(
                _llm_url(settings.llm_base_url or ""),
                json=payload,
                headers={
                    "Authorization": f"Bearer {settings.llm_api_key}",
                    "Content-Type": "application/json",
                },
            )
    except httpx.HTTPError:
        logger.warning("llm request failed")
        raise AppError(503, "UPSTREAM_UNAVAILABLE", "语言模型暂时不可用") from None
    if response.status_code >= 400:
        logger.warning("llm upstream status=%s", response.status_code)
        raise AppError(503, "UPSTREAM_UNAVAILABLE", "语言模型暂时不可用")
    try:
        content = response.json()["choices"][0]["message"]["content"]
        parsed = _parse_model_json(content)
    except (KeyError, IndexError, TypeError, ValueError):
        logger.warning("llm response was not usable json")
        raise AppError(503, "UPSTREAM_UNAVAILABLE", "语言模型返回无法解析") from None
    return guard_model_payload(parsed, record)


def answer_question(settings: Settings, record: dict[str, Any], question: str) -> AskResponse:
    decided = local_decision(question, record)
    if decided is not None:
        return decided
    if not settings.llm_ready:
        raise AppError(503, "UPSTREAM_UNAVAILABLE", "LLM 未配置，暂时无法生成回答")
    return call_llm(settings, record, question)
