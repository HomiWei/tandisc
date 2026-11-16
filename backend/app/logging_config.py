"""JSON logs on stdout. Messages are redacted before they are written."""

import json
import logging
import re
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

_BEARER = re.compile(r"(Bearer\s+)\S+", re.IGNORECASE)
_ASSIGNMENT = re.compile(
    r"((?:api[_-]?key|token|secret|password|authorization)\s*[=:]\s*)\S+",
    re.IGNORECASE,
)


def redact(message: str) -> str:
    message = _BEARER.sub(r"\1[redacted]", message)
    message = _ASSIGNMENT.sub(r"\1[redacted]", message)
    return message


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "ts": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": redact(record.getMessage()),
        }
        if record.exc_info:
            payload["exc"] = redact(self.formatException(record.exc_info))
        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> None:
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.handlers = [handler]
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
