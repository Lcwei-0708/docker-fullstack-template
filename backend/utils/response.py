from datetime import datetime
from typing import TypeVar

from pydantic import BaseModel, RootModel

T = TypeVar("T")


class APIResponse[T](BaseModel):
    """Generic API response wrapper that maintains consistent response structure"""

    code: int
    message: str
    data: T | None = None


class ValidationErrorData(RootModel[dict[str, str]]):
    """Model for validation error data structure"""

    pass


def is_openapi_examples(example: dict) -> bool:
    """
    Detect OpenAPI Media Type ``examples`` (named map with dropdown in Swagger UI).

    Expected shape:
        {
          "caseA": {"summary": "...", "value": {...}},
          "caseB": {"value": {...}},
        }
    """
    if not isinstance(example, dict) or not example:
        return False
    if "code" in example or "message" in example or "data" in example:
        return False
    return all(isinstance(item, dict) and "value" in item for item in example.values())


def make_response_doc(
    description: str, model: type | None = None, example: dict | None = None
) -> dict:
    """Create OpenAPI response documentation with model and example(s)"""
    doc = {"description": description}
    if model:
        doc["model"] = APIResponse[model]
    if example:
        media = {"examples": example} if is_openapi_examples(example) else {"example": example}
        doc["content"] = {"application/json": media}
    return doc


def make_error_examples(code: int, cases: dict[str, str]) -> dict:
    """
    Build OpenAPI named ``examples`` for simple error responses.

    Example:
        make_error_examples(401, {
            "invalidSession": "Invalid or expired session",
            "invalidCsrf": "Invalid or expired CSRF token",
        })
    """
    return {
        key: {
            "summary": message,
            "value": {"code": code, "message": message, "data": None},
        }
        for key, message in cases.items()
    }


def parse_responses(custom: dict, default: dict = None) -> dict:
    """
    Parse and merge responses. Supports:
    - 2-tuple: (description, model) - auto-generates example
    - 3-tuple: (description, model, example) - single example dict,
      or OpenAPI named ``examples`` map (Swagger UI dropdown)
    - string: description only - creates simple error response
    """
    # Merge default responses first, then override with custom ones
    merged = {}
    if default:
        merged.update(default)
    if custom:
        merged.update(custom)

    result = {}
    for code, val in merged.items():
        if isinstance(val, tuple):
            if len(val) == 2:
                desc, model = val
                if model is None:
                    data_example = None
                else:
                    try:
                        schema = model.model_json_schema()
                        data_example = generate_example_from_schema(schema)
                    except Exception:
                        data_example = None

                example = {"code": code, "message": desc, "data": data_example}
                result[code] = make_response_doc(desc, model, example)
            elif len(val) == 3:
                desc, model, example = val
                # Auto-fill only for a single response body example
                if not is_openapi_examples(example):
                    if "code" not in example:
                        example["code"] = code
                    if "message" not in example:
                        example["message"] = desc
                result[code] = make_response_doc(desc, model, example)
        elif isinstance(val, str):
            example = {"code": code, "message": val, "data": None}
            result[code] = make_response_doc(val, None, example)
        else:
            result[code] = val
    return result


def generate_example_from_schema(schema: dict) -> dict:
    """Generate example data from JSON schema object properties"""
    if schema.get("type") == "object":
        properties = schema.get("properties", {})
        example = {}
        for key, prop in properties.items():
            example[key] = generate_property_example(prop, key, schema)
        return example
    return None


def generate_property_example(prop: dict, key: str = "", full_schema: dict = None):
    """Generate example value for a single property based on its type and field name"""
    # Handle $ref references first (for nested objects)
    if prop.get("$ref"):
        referenced_schema = resolve_ref(prop["$ref"], full_schema)
        if referenced_schema:
            return generate_example_from_schema(referenced_schema)
        return None

    prop_type = prop.get("type")

    if prop_type == "string":
        if key == "id":
            return "123e4567-e89b-12d3-a456-426614174000"
        elif "email" in key.lower():
            return "user@example.com"
        elif key == "phone":
            return "123456789"
        elif key == "created_at":
            return datetime.now().astimezone().isoformat()
        elif key == "updated_at":
            return datetime.now().astimezone().isoformat()
        elif key == "expires_at":
            return datetime.now().astimezone().isoformat()
        else:
            return f"Example {key.replace('_', ' ').title()}"
    elif prop_type == "integer":
        if key in ["per_page", "total_pages"]:
            return 10
        elif key == "page":
            return 1
        else:
            return 100
    elif prop_type == "number":
        return 123.45
    elif prop_type == "boolean":
        return True
    elif prop_type == "array":
        items_schema = prop.get("items", {})
        # Handle $ref references in array items (e.g., List[UserRead])
        if items_schema.get("$ref"):
            referenced_schema = resolve_ref(items_schema["$ref"], full_schema)
            if referenced_schema:
                item_example = generate_example_from_schema(referenced_schema)
                return [item_example] if item_example else []
        return []
    elif prop_type == "object":
        return generate_example_from_schema(prop)
    elif prop.get("format") == "date-time":
        return datetime.now().astimezone().isoformat()
    elif prop.get("anyOf"):
        options = prop.get("anyOf", [])
        for option in options:
            if option.get("type") != "null":
                return generate_property_example(option, key, full_schema)
        return None
    else:
        return None


def resolve_ref(ref_path: str, schema: dict) -> dict:
    """
    Resolve JSON Schema $ref references to actual schema definitions
    """
    if not ref_path.startswith("#/"):
        return None

    # Parse reference path: "#/$defs/UserRead" -> ["$defs", "UserRead"]
    path_parts = ref_path[2:].split("/")
    current = schema

    # Navigate through nested dict structure following the path
    for part in path_parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            # Reference not found
            return None

    if isinstance(current, dict):
        return current
    else:
        return None


common_responses = {
    401: (
        "Invalid or expired token",
        APIResponse[None],
        {"code": 401, "message": "Invalid or expired token", "data": None},
    ),
    403: (
        "Permission denied",
        APIResponse[None],
        {"code": 403, "message": "Permission denied", "data": None},
    ),
    422: (
        "Validation Error",
        APIResponse[ValidationErrorData],
        {"code": 422, "message": "Validation Error", "data": {"body.params": "field required"}},
    ),
    429: (
        "Too many requests. Try again later.",
        APIResponse[None],
        {"code": 429, "message": "Too many requests. Try again later.", "data": None},
    ),
    500: (
        "Internal Server Error",
        APIResponse[None],
        {"code": 500, "message": "Internal Server Error", "data": None},
    ),
}
