from pydantic import BaseModel, Field
from typing import Optional, Dict, List

class RoleResponse(BaseModel):
    id: str = Field(..., description="Role ID")
    name: str = Field(..., description="Role name")
    description: Optional[str] = Field(None, description="Role description")

class RolesListResponse(BaseModel):
    roles: List[RoleResponse] = Field(..., description="List of roles")

class RoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Role name")
    description: Optional[str] = Field(None, max_length=500, description="Role description")

class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Role name")
    description: Optional[str] = Field(None, max_length=500, description="Role description")

class RoleAttributesMapping(BaseModel):
    attributes: Dict[str, bool] = Field(
        ..., 
        description="Role attributes mapping (attribute_name: value)",
        example={
            "view-users": True,
            "manage-users": False,
            "view-roles": True
        }
    )
    
    @classmethod
    def get_example_response(cls):
        return {
            "code": 200,
            "message": "Role attributes mapping example",
            "data": {
                "attributes": {
                    "view-users": True,
                    "manage-users": False,
                    "view-roles": True
                }
            }
        }

class RoleAttributeDetail(BaseModel):
    name: str = Field(..., description="Attribute name", example="view-users")
    value: bool = Field(..., description="Whether the role has this attribute", example=True)


class RoleAttributesGroup(BaseModel):
    group: str = Field(..., description="Top-level group key", example="user-role-management")
    categories: Dict[str, List[RoleAttributeDetail]] = Field(..., description="Categories inside this group (category -> attributes)")


class RoleAttributesGroupedResponse(BaseModel):
    groups: List[RoleAttributesGroup] = Field(..., description="Role attributes grouped by group and category")

    @classmethod
    def get_example_response(cls):
        return {
            "code": 200,
            "message": "Successfully retrieved role attributes mapping",
            "data": {
                "groups": [
                    {
                        "group": "user-role-management",
                        "categories": {
                            "user": [
                                {
                                    "name": "view-users",
                                    "value": True
                                },
                                {
                                    "name": "manage-users",
                                    "value": False
                                }
                            ],
                            "role": [
                                {
                                    "name": "view-roles",
                                    "value": True
                                }
                            ]
                        }
                    }
                ]
            }
        }

class AttributeMappingResult(BaseModel):
    attribute_id: str = Field(..., description="Attribute ID")
    status: str = Field(..., description="Processing status: success, failed", pattern="^(success|failed)$")
    message: str = Field(..., description="Result message")

class RoleAttributeMappingBatchResponse(BaseModel):
    results: List[AttributeMappingResult] = Field(..., description="Individual attribute mapping results")
    total_attributes: int = Field(..., description="Total number of attributes processed")
    success_count: int = Field(..., description="Number of successfully processed attributes")
    failed_count: int = Field(..., description="Number of failed attributes")

class PermissionCheckRequest(BaseModel):
    attributes: Optional[List[str]] = Field(
        None, 
        min_items=1,
        description="List of permission attributes to check. If not provided, returns all user permissions.",
        example=["view-users", "manage-roles"]
    )

class PermissionCheckResponse(BaseModel):
    permissions: Dict[str, bool] = Field(
        ..., 
        description="Permission check results (attribute_name: has_permission)",
        example={
            "view-users": True,
            "manage-users": False,
            "view-roles": True,
            "manage-roles": False
        }
    )
    
    @classmethod
    def get_example_response(cls):
        return {
            "code": 200,
            "message": "User permissions retrieved",
            "data": {
                "permissions": {
                    "view-users": True,
                    "manage-users": False,
                    "view-roles": True,
                    "manage-roles": False
                }
            }
        }

role_attributes_success_response_example = {
    "code": 200,
    "message": "All role attributes processed successfully",
    "data": {
        "results": [
            {
                "attribute_id": "attr-001",
                "status": "success",
                "message": "Updated successfully"
            },
            {
                "attribute_id": "attr-002", 
                "status": "success",
                "message": "Updated successfully"
            }
        ],
        "total_attributes": 2,
        "success_count": 2,
        "failed_count": 0
    }
}

role_attributes_partial_response_example = {
    "code": 207,
    "message": "Role attributes processed with partial success",
    "data": {
        "results": [
            {
                "attribute_id": "attr-001",
                "status": "success",
                "message": "Updated successfully"
            },
            {
                "attribute_id": "attr-002",
                "status": "failed",
                "message": "Invalid attribute ID"
            }
        ],
        "total_attributes": 2,
        "success_count": 1,
        "failed_count": 1
    }
}

role_attributes_failed_response_example = {
    "code": 400,
    "message": "All role attributes failed to process",
    "data": {
        "results": [
            {
                "attribute_id": "invalid-attr-001",
                "status": "failed",
                "message": "Invalid attribute ID"
            },
            {
                "attribute_id": "invalid-attr-002",
                "status": "failed", 
                "message": "Invalid attribute ID"
            }
        ],
        "total_attributes": 2,
        "success_count": 0,
        "failed_count": 2
    }
}