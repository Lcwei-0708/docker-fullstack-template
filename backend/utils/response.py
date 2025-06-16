from pydantic import BaseModel, RootModel
from typing import Any, Dict, Optional, Type, TypeVar, Generic, List

T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
    code: int
    message: str
    data: Optional[T] = None

class ValidationErrorData(RootModel[dict[str, str]]):
    pass

def make_response_doc(description: str, model: Optional[Type] = None, example: Optional[dict] = None) -> dict:
    doc = {
        "description": description,
    }
    if model:
        doc["model"] = model
    if example:
        doc["content"] = {
            "application/json": {
                "example": example
            }
        }
    return doc

def parse_responses(custom: dict, default: dict = None) -> dict:
    """
    custom: The dict you write in controller, e.g.
        {
            200: ("Success", APIResponse[UserRead]),
            401: "Invalid Token",
            404: ("Not found", APIResponse[None], {"code":404,"message":"Not found","data":None}),
        }
    default: The default common_responses
    """
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
                result[code] = make_response_doc(desc, model)
            elif len(val) == 3:
                desc, model, example = val
                if "code" not in example:
                    example["code"] = code
                result[code] = make_response_doc(desc, model, example)
        elif isinstance(val, str):
            example = {
                "code": code,
                "message": val,
                "data": None
            }
            result[code] = make_response_doc(val, None, example)
        else:
            # direct dict
            result[code] = val
    return result

common_responses = {
    422: (
        "Validation Error",
        APIResponse[ValidationErrorData],
        {
            "code": 422,
            "message": "Validation Error",
            "data": {
                "body.username": "field required"
            }
        }
    ),
    500: (
        "Internal Server Error",
        APIResponse[None],
        {
            "code": 500,
            "message": "Internal Server Error",
            "data": None
        }
    )
}