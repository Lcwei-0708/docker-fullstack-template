import json
import re
from typing import Any
from urllib.parse import parse_qs

REDACTED = "[REDACTED]"
ELLIPSIS = "..."
PREVIEW_CHARS = 8192
JWT_RE = re.compile(r"^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$")
SENSITIVE_TEXT_RE = re.compile(
    r"(?i)\b(password|passwd|pwd|secret|token|authorization|api[_-]?key)\b\s*[:=]\s*\S+"
)
SENSITIVE_KEY_MARKERS = (
    "password",
    "passwd",
    "pwd",
    "secret",
    "token",
    "authorization",
    "cookie",
    "apikey",
    "setcookie",
    "privatekey",
    "csrf",
    "creditcard",
    "cardnumber",
    "cvv",
    "ssn",
)
SKIP_CONTENT_TYPES = (
    "multipart/",
    "image/",
    "audio/",
    "video/",
    "octet-stream",
    "gzip",
    "zip",
    "text/event-stream",
)


def _normalize_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]", "", key.lower())


def is_sensitive_key(key: str) -> bool:
    normalized = _normalize_key(str(key))
    return any(marker in normalized for marker in SENSITIVE_KEY_MARKERS)


def should_omit_body(content_type: str) -> bool:
    lowered = (content_type or "").lower()
    return any(kind in lowered for kind in SKIP_CONTENT_TYPES)


def quote_log_field(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def format_log_value(value: str) -> str:
    """Wrap values so Grafana can extract original JSON, including spaces."""
    compact = value.replace("\n", "\\n").replace("\r", "").replace(">>", "\\u003e\\u003e")
    return f"<<{compact}>>"


def _redact_string(value: str) -> str:
    stripped = value.strip()
    if stripped.lower().startswith("bearer ") or JWT_RE.match(stripped):
        return REDACTED
    return value


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: REDACTED if is_sensitive_key(str(key)) else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str):
        return _redact_string(value)
    return value


def _redact_loose_text(text: str) -> str:
    return SENSITIVE_TEXT_RE.sub(lambda match: f"{match.group(1)}={REDACTED}", text)


def _decode(raw: bytes, max_bytes: int) -> tuple[str, bool]:
    truncated = len(raw) > max_bytes
    return raw[:max_bytes].decode("utf-8", errors="replace"), truncated


def _loads_json_prefix(text: str) -> Any | None:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    in_string = False
    escape = False
    stack: list[str] = []
    for char in text:
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            stack.append("}")
        elif char == "[":
            stack.append("]")
        elif stack and char == stack[-1]:
            stack.pop()

    candidate = text.rstrip()
    if in_string:
        candidate += '"'
    candidate = re.sub(r",\s*$", "", candidate)
    candidate += "".join(reversed(stack))
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


def _with_ellipsis(rendered: str, limit: int = PREVIEW_CHARS) -> str:
    if len(rendered) <= limit:
        return rendered + ELLIPSIS
    cutoff = max(16, limit - len(ELLIPSIS))
    preview = rendered[:cutoff]
    for separator in ("},", "],", ",", "}", "]"):
        index = preview.rfind(separator)
        if index >= cutoff // 3:
            preview = preview[: index + len(separator)].rstrip(",")
            break
    return preview + ELLIPSIS


def sanitize_body(raw: bytes, content_type: str, max_bytes: int = 8192) -> str:
    if not raw:
        return ""
    if should_omit_body(content_type):
        return "[omitted]"

    text, truncated = _decode(raw, max_bytes)
    lowered = (content_type or "").lower()
    payload: Any = None
    parsed = False

    if "application/json" in lowered or text[:1] in "{[":
        parsed_json = _loads_json_prefix(text)
        if parsed_json is not None:
            payload = redact(parsed_json)
            parsed = True
    elif "application/x-www-form-urlencoded" in lowered:
        parsed_form = {
            key: values[-1] if values else ""
            for key, values in parse_qs(text, keep_blank_values=True).items()
        }
        payload = redact(parsed_form)
        parsed = True

    if not parsed:
        preview = _redact_loose_text(text).replace("\n", "\\n")
        if truncated:
            return _with_ellipsis(preview)
        return preview

    if isinstance(payload, (dict, list)):
        rendered = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    else:
        rendered = str(payload).replace("\n", "\\n")

    if truncated or len(rendered) > PREVIEW_CHARS:
        return _with_ellipsis(rendered)
    return rendered


def sanitize_query(query_params: Any) -> str:
    data = {str(key): value for key, value in dict(query_params).items()}
    if not data:
        return ""
    return json.dumps(redact(data), ensure_ascii=False, separators=(",", ":"))
