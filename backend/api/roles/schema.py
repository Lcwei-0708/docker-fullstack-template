from pydantic import BaseModel, Field
from typing import Optional, Dict, List

class RoleResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None

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
        description="Role attributes mapping (attribute_id: value)",
        example={
            "attribute_id_1": True,
            "attribute_id_2": False,
            "attribute_id_3": False
        }
    )
    
    @classmethod
    def get_example_response(cls):
        return {
            "code": 200,
            "message": "Successfully retrieved role attributes mapping",
            "data": {
                "attributes": {
                    "attribute_id_1": True,
                    "attribute_id_2": False,
                    "attribute_id_3": False
                }
            }
        }

class AttributeMappingResult(BaseModel):
    attribute_id: str = Field(..., description="Attribute ID")
    status: str = Field(..., description="Processing status: success, failed")
    message: str = Field(..., description="Result message")

class RoleAttributeMappingBatchResponse(BaseModel):
    results: List[AttributeMappingResult] = Field(..., description="Individual attribute mapping results")
    total_attributes: int = Field(..., description="Total number of attributes processed")
    success_count: int = Field(..., description="Number of successfully processed attributes")
    failed_count: int = Field(..., description="Number of failed attributes")

class PermissionCheckRequest(BaseModel):
    attributes: List[str] = Field(
        ..., 
        min_items=1,
        description="List of permission attributes to check",
        example=["view-users", "manage-roles"]
    )

class PermissionCheckResponse(BaseModel):
    permissions: Dict[str, bool] = Field(..., description="Permission check results (attribute: has_permission)")