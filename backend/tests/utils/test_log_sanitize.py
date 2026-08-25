import json

from utils.log_sanitize import (
    ELLIPSIS,
    PREVIEW_CHARS,
    REDACTED,
    format_log_value,
    quote_log_field,
    redact,
    sanitize_body,
    sanitize_query,
    should_omit_body,
)


class TestLogSanitize:
    def test_redacts_password_and_token_keys(self):
        payload = {
            "email": "user@example.com",
            "password": "super-secret",
            "access_token": "abc.def.ghi",
            "nested": {"refresh_token": "keep-me-hidden", "name": "Ada"},
        }

        redacted = redact(payload)

        assert redacted["email"] == "user@example.com"
        assert redacted["password"] == REDACTED
        assert redacted["access_token"] == REDACTED
        assert redacted["nested"]["refresh_token"] == REDACTED
        assert redacted["nested"]["name"] == "Ada"

    def test_redacts_jwt_and_bearer_values(self):
        jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.abc"
        assert redact({"note": jwt})["note"] == REDACTED
        assert redact({"note": f"Bearer {jwt}"})["note"] == REDACTED

    def test_sanitize_json_body(self):
        raw = json.dumps({"email": "a@b.c", "password": "secret"}).encode()
        rendered = sanitize_body(raw, "application/json")

        assert "secret" not in rendered
        assert REDACTED in rendered
        assert "a@b.c" in rendered

    def test_sanitize_form_body(self):
        raw = b"username=ada&password=secret"
        rendered = sanitize_body(raw, "application/x-www-form-urlencoded")

        assert "secret" not in rendered
        assert "ada" in rendered
        assert REDACTED in rendered

    def test_omits_multipart_and_binary(self):
        assert should_omit_body("multipart/form-data; boundary=abc")
        assert sanitize_body(b"file-bytes", "image/png") == "[omitted]"

    def test_unparsed_truncated_body_keeps_prefix(self):
        raw = b"password=super-secret-and-then-some" + b"x" * 100
        rendered = sanitize_body(raw, "text/plain", max_bytes=10)

        assert rendered.endswith("...")
        assert rendered != "..."
        assert "super-secret" not in rendered

    def test_truncated_json_array_uses_ellipsis(self):
        users = [{"id": index, "email": f"user{index}@example.com"} for index in range(40)]
        raw = json.dumps(users, separators=(",", ":")).encode()
        rendered = sanitize_body(raw, "application/json", max_bytes=120)

        assert rendered.endswith("...")
        assert rendered != "..."
        assert "[truncated]" not in rendered
        assert "email" in rendered

    def test_loose_text_redacts_password_assignment(self):
        rendered = sanitize_body(b"user=ada password=secret", "text/plain")
        assert "secret" not in rendered
        assert REDACTED in rendered

    def test_sanitize_query(self):
        rendered = sanitize_query({"email": "a@b.c", "token": "abc"})
        assert "a@b.c" in rendered
        assert "abc" not in rendered
        assert REDACTED in rendered
        assert sanitize_query({}) == ""

    def test_unrepairable_truncated_json_falls_back_to_text(self):
        rendered = sanitize_body(b'{"a":', "application/json")
        assert rendered.startswith("{")

    def test_quote_log_field_escapes_quotes(self):
        assert quote_log_field('{"a":"b"}') == '"{\\"a\\":\\"b\\"}"'

    def test_format_log_value_wraps_json_with_spaces(self):
        json_body = '{"code":200,"message":"Successfully retrieved"}'
        assert format_log_value(json_body) == f"<<{json_body}>>"
        assert format_log_value("[omitted]") == "<<[omitted]>>"

    def test_empty_body(self):
        assert sanitize_body(b"", "application/json") == ""

    def test_truncated_json_string_with_escape(self):
        raw = b'{"note":"foo\\\\bar'
        rendered = sanitize_body(raw, "application/json")
        assert "foo" in rendered

    def test_json_scalar_is_stringified(self):
        assert sanitize_body(b"true", "application/json") == "True"
        assert sanitize_body(b'"hello"', "application/json") == "hello"

    def test_long_json_uses_ellipsis_at_separator(self):
        payload = {
            "items": [{"id": index, "email": f"user{index}@example.com"} for index in range(400)]
        }
        raw = json.dumps(payload, separators=(",", ":")).encode()
        rendered = sanitize_body(raw, "application/json", max_bytes=len(raw) + 1)
        assert len(json.dumps(payload, separators=(",", ":"))) > PREVIEW_CHARS
        assert rendered.endswith(ELLIPSIS)
        assert rendered != ELLIPSIS
