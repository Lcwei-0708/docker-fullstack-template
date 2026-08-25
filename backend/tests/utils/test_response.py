from datetime import datetime

from pydantic import BaseModel

from utils.response import (
    generate_example_from_schema,
    generate_property_example,
    is_openapi_examples,
    make_error_examples,
    make_response_doc,
    parse_responses,
    resolve_ref,
)


class SampleUser(BaseModel):
    id: str
    email: str


class TestIsOpenApiExamples:
    def test_rejects_empty_or_response_body(self):
        assert is_openapi_examples({}) is False
        assert is_openapi_examples({"code": 200, "message": "ok"}) is False
        assert is_openapi_examples("not-a-dict") is False

    def test_accepts_named_examples_map(self):
        example = {
            "ok": {"summary": "success", "value": {"code": 200}},
            "other": {"value": {"code": 201}},
        }
        assert is_openapi_examples(example) is True


class TestMakeResponseHelpers:
    def test_make_error_examples(self):
        examples = make_error_examples(401, {"invalidSession": "Invalid session"})
        assert examples["invalidSession"]["summary"] == "Invalid session"
        assert examples["invalidSession"]["value"]["code"] == 401

    def test_make_response_doc_with_named_examples(self):
        example = {"ok": {"value": {"code": 200, "message": "ok", "data": None}}}
        doc = make_response_doc("OK", None, example)
        assert "examples" in doc["content"]["application/json"]


class TestParseResponses:
    def test_merges_default_and_custom(self):
        result = parse_responses(
            {200: "Custom OK"},
            default={401: "Unauthorized"},
        )
        assert 200 in result
        assert 401 in result

    def test_two_tuple_without_model(self):
        result = parse_responses({204: ("No Content", None)})
        assert result[204]["description"] == "No Content"

    def test_two_tuple_with_model(self):
        result = parse_responses({200: ("User", SampleUser)})
        assert result[200]["model"] is not None
        assert result[200]["content"]["application/json"]["example"]["data"]["id"]

    def test_three_tuple_fills_missing_fields(self):
        result = parse_responses({201: ("Created", None, {"data": {"id": "1"}})})
        example = result[201]["content"]["application/json"]["example"]
        assert example["code"] == 201
        assert example["message"] == "Created"

    def test_three_tuple_named_examples(self):
        named = make_error_examples(401, {"expired": "Token expired"})
        result = parse_responses({401: ("Unauthorized", None, named)})
        assert "examples" in result[401]["content"]["application/json"]

    def test_string_and_passthrough(self):
        result = parse_responses(
            {
                400: "Bad Request",
                418: {"description": "teapot"},
            }
        )
        assert result[400]["description"] == "Bad Request"
        assert result[418]["description"] == "teapot"


class TestGenerateExampleFromSchema:
    def test_returns_none_for_non_object(self):
        assert generate_example_from_schema({"type": "string"}) is None

    def test_property_examples_by_name_and_type(self):
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "email": {"type": "string"},
                "phone": {"type": "string"},
                "created_at": {"type": "string"},
                "updated_at": {"type": "string"},
                "expires_at": {"type": "string"},
                "title": {"type": "string"},
                "page": {"type": "integer"},
                "per_page": {"type": "integer"},
                "count": {"type": "integer"},
                "ratio": {"type": "number"},
                "active": {"type": "boolean"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "nested": {"type": "object", "properties": {"ok": {"type": "boolean"}}},
                "when": {"format": "date-time"},
                "maybe": {"anyOf": [{"type": "null"}, {"type": "integer"}]},
                "empty_any": {"anyOf": [{"type": "null"}]},
                "unknown": {},
            },
        }
        example = generate_example_from_schema(schema)
        assert example["id"].startswith("123e4567")
        assert example["email"] == "user@example.com"
        assert example["phone"] == "123456789"
        datetime.fromisoformat(example["created_at"])
        datetime.fromisoformat(example["updated_at"])
        datetime.fromisoformat(example["expires_at"])
        assert example["title"] == "Example Title"
        assert example["page"] == 1
        assert example["per_page"] == 10
        assert example["count"] == 100
        assert example["ratio"] == 123.45
        assert example["active"] is True
        assert example["tags"] == []
        assert example["nested"]["ok"] is True
        datetime.fromisoformat(example["when"])
        assert example["maybe"] == 100
        assert example["empty_any"] is None
        assert example["unknown"] is None

    def test_resolves_object_and_array_refs(self):
        schema = {
            "type": "object",
            "properties": {
                "user": {"$ref": "#/$defs/User"},
                "missing": {"$ref": "#/$defs/Nope"},
                "users": {"type": "array", "items": {"$ref": "#/$defs/User"}},
                "empty_items": {"type": "array", "items": {"$ref": "#/$defs/Nope"}},
            },
            "$defs": {
                "User": {"type": "object", "properties": {"id": {"type": "string"}}},
            },
        }
        example = generate_example_from_schema(schema)
        assert example["user"]["id"].startswith("123e4567")
        assert example["missing"] is None
        assert example["users"][0]["id"].startswith("123e4567")
        assert example["empty_items"] == []


class TestResolveRef:
    def test_rejects_external_or_missing_refs(self):
        assert resolve_ref("https://example.com/schema", {}) is None
        assert resolve_ref("#/$defs/missing", {"$defs": {}}) is None

    def test_returns_none_for_non_dict_leaf(self):
        assert resolve_ref("#/$defs/flag", {"$defs": {"flag": True}}) is None
