import pytest
from pydantic import ValidationError
from api.roles.schema import (
    RoleResponse,
    RolesListResponse,
    RoleCreate,
    RoleUpdate,
    RoleAttributesMapping,
    RoleAttributesGroupedResponse,
    AttributeMappingResult,
    RoleAttributeMappingBatchResponse,
    PermissionCheckRequest,
    PermissionCheckResponse,
)


class TestRoleResponse:
    """Test RoleResponse schema validation"""

    def test_role_response_valid_data(self):
        """Test RoleResponse with valid data"""
        role_data = {
            "id": "role-123",
            "name": "admin",
            "description": "Administrator role",
        }

        role = RoleResponse(**role_data)
        assert role.id == "role-123"
        assert role.name == "admin"
        assert role.description == "Administrator role"

    def test_role_response_minimal_data(self):
        """Test RoleResponse with minimal required data"""
        role_data = {"id": "role-456", "name": "user"}

        role = RoleResponse(**role_data)
        assert role.id == "role-456"
        assert role.name == "user"
        assert role.description is None

    def test_role_response_missing_required_fields(self):
        """Test RoleResponse with missing required fields"""
        with pytest.raises(ValidationError) as exc_info:
            RoleResponse(id="role-123")

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "missing"
        assert errors[0]["loc"] == ("name",)


class TestRolesListResponse:
    """Test RolesListResponse schema validation"""

    def test_roles_list_response_valid_data(self):
        """Test RolesListResponse with valid data"""
        roles_data = {
            "roles": [
                {"id": "role-1", "name": "admin", "description": "Admin role"},
                {"id": "role-2", "name": "user", "description": "User role"},
            ]
        }

        response = RolesListResponse(**roles_data)
        assert len(response.roles) == 2
        assert response.roles[0].name == "admin"
        assert response.roles[1].name == "user"

    def test_roles_list_response_empty_list(self):
        """Test RolesListResponse with empty roles list"""
        roles_data = {"roles": []}
        response = RolesListResponse(**roles_data)
        assert len(response.roles) == 0

    def test_roles_list_response_missing_roles_field(self):
        """Test RolesListResponse with missing roles field"""
        with pytest.raises(ValidationError) as exc_info:
            RolesListResponse()

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "missing"
        assert errors[0]["loc"] == ("roles",)


class TestRoleCreate:
    """Test RoleCreate schema validation"""

    def test_role_create_valid_data(self):
        """Test RoleCreate with valid data"""
        role_data = {
            "name": "manager",
            "description": "Manager role with special permissions",
        }

        role = RoleCreate(**role_data)
        assert role.name == "manager"
        assert role.description == "Manager role with special permissions"

    def test_role_create_minimal_data(self):
        """Test RoleCreate with minimal required data"""
        role_data = {"name": "guest"}
        role = RoleCreate(**role_data)
        assert role.name == "guest"
        assert role.description is None

    def test_role_create_name_validation(self):
        """Test RoleCreate name field validation"""
        # Test empty name
        with pytest.raises(ValidationError) as exc_info:
            RoleCreate(name="")
        errors = exc_info.value.errors()
        assert any(error["type"] == "string_too_short" for error in errors)

        # Test name too long
        with pytest.raises(ValidationError) as exc_info:
            RoleCreate(name="a" * 101)
        errors = exc_info.value.errors()
        assert any(error["type"] == "string_too_long" for error in errors)

    def test_role_create_description_validation(self):
        """Test RoleCreate description field validation"""
        # Test description too long
        with pytest.raises(ValidationError) as exc_info:
            RoleCreate(name="test", description="a" * 501)
        errors = exc_info.value.errors()
        assert any(error["type"] == "string_too_long" for error in errors)

    def test_role_create_missing_name(self):
        """Test RoleCreate with missing required name field"""
        with pytest.raises(ValidationError) as exc_info:
            RoleCreate(description="Test description")

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "missing"
        assert errors[0]["loc"] == ("name",)


class TestRoleUpdate:
    """Test RoleUpdate schema validation"""

    def test_role_update_valid_data(self):
        """Test RoleUpdate with valid data"""
        role_data = {"name": "updated_manager", "description": "Updated manager role"}

        role = RoleUpdate(**role_data)
        assert role.name == "updated_manager"
        assert role.description == "Updated manager role"

    def test_role_update_partial_data(self):
        """Test RoleUpdate with partial data"""
        role_data = {"name": "updated_name"}
        role = RoleUpdate(**role_data)
        assert role.name == "updated_name"
        assert role.description is None

    def test_role_update_empty_data(self):
        """Test RoleUpdate with empty data"""
        role = RoleUpdate()
        assert role.name is None
        assert role.description is None

    def test_role_update_name_validation(self):
        """Test RoleUpdate name field validation"""
        # Test empty name
        with pytest.raises(ValidationError) as exc_info:
            RoleUpdate(name="")
        errors = exc_info.value.errors()
        assert any(error["type"] == "string_too_short" for error in errors)

        # Test name too long
        with pytest.raises(ValidationError) as exc_info:
            RoleUpdate(name="a" * 101)
        errors = exc_info.value.errors()
        assert any(error["type"] == "string_too_long" for error in errors)


class TestRoleAttributesMapping:
    """Test RoleAttributesMapping schema validation"""

    def test_role_attributes_mapping_valid_data(self):
        """Test RoleAttributesMapping with valid data"""
        attributes_data = {"attributes": {"attr1": True, "attr2": False, "attr3": True}}

        mapping = RoleAttributesMapping(**attributes_data)
        assert mapping.attributes["attr1"] is True
        assert mapping.attributes["attr2"] is False
        assert mapping.attributes["attr3"] is True

    def test_role_attributes_mapping_empty_attributes(self):
        """Test RoleAttributesMapping with empty attributes"""
        attributes_data = {"attributes": {}}
        mapping = RoleAttributesMapping(**attributes_data)
        assert len(mapping.attributes) == 0

    def test_role_attributes_mapping_missing_attributes(self):
        """Test RoleAttributesMapping with missing attributes field"""
        with pytest.raises(ValidationError) as exc_info:
            RoleAttributesMapping()

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "missing"
        assert errors[0]["loc"] == ("attributes",)

    def test_get_example_response(self):
        """Test get_example_response class method"""
        example = RoleAttributesMapping.get_example_response()
        assert "code" in example
        assert "message" in example
        assert "data" in example
        assert example["code"] == 200
        assert "attributes" in example["data"]


class TestRoleAttributesGroupedResponse:
    """Test RoleAttributesGroupedResponse schema validation"""

    def test_role_attributes_grouped_response_valid_data(self):
        data = {
            "groups": [
                {
                    "group": "user-role-management",
                    "categories": {
                        "user": [
                            {"name": "view-users", "value": True},
                            {"name": "manage-users", "value": False},
                        ]
                    },
                }
            ]
        }

        result = RoleAttributesGroupedResponse(**data)
        assert len(result.groups) == 1
        assert result.groups[0].group == "user-role-management"
        assert "user" in result.groups[0].categories
        assert result.groups[0].categories["user"][0].name == "view-users"
        assert result.groups[0].categories["user"][0].value is True

    def test_get_example_response(self):
        example = RoleAttributesGroupedResponse.get_example_response()
        assert example["code"] == 200
        assert "groups" in example["data"]


class TestAttributeMappingResult:
    """Test AttributeMappingResult schema validation"""

    def test_attribute_mapping_result_valid_data(self):
        """Test AttributeMappingResult with valid data"""
        result_data = {
            "attribute_id": "attr-123",
            "status": "success",
            "message": "Updated successfully",
        }

        result = AttributeMappingResult(**result_data)
        assert result.attribute_id == "attr-123"
        assert result.status == "success"
        assert result.message == "Updated successfully"

    def test_attribute_mapping_result_failed_status(self):
        """Test AttributeMappingResult with failed status"""
        result_data = {
            "attribute_id": "attr-456",
            "status": "failed",
            "message": "Invalid attribute ID",
        }

        result = AttributeMappingResult(**result_data)
        assert result.attribute_id == "attr-456"
        assert result.status == "failed"
        assert result.message == "Invalid attribute ID"

    def test_attribute_mapping_result_missing_fields(self):
        """Test AttributeMappingResult with missing required fields"""
        with pytest.raises(ValidationError) as exc_info:
            AttributeMappingResult(attribute_id="attr-123")

        errors = exc_info.value.errors()
        assert len(errors) == 2  # status and message missing


class TestRoleAttributeMappingBatchResponse:
    """Test RoleAttributeMappingBatchResponse schema validation"""

    def test_batch_response_valid_data(self):
        """Test RoleAttributeMappingBatchResponse with valid data"""
        results = [
            AttributeMappingResult(
                attribute_id="attr1", status="success", message="Updated successfully"
            ),
            AttributeMappingResult(
                attribute_id="attr2", status="failed", message="Invalid attribute ID"
            ),
        ]

        batch_data = {
            "results": results,
            "total_attributes": 2,
            "success_count": 1,
            "failed_count": 1,
        }

        response = RoleAttributeMappingBatchResponse(**batch_data)
        assert len(response.results) == 2
        assert response.total_attributes == 2
        assert response.success_count == 1
        assert response.failed_count == 1

    def test_batch_response_empty_results(self):
        """Test RoleAttributeMappingBatchResponse with empty results"""
        batch_data = {
            "results": [],
            "total_attributes": 0,
            "success_count": 0,
            "failed_count": 0,
        }

        response = RoleAttributeMappingBatchResponse(**batch_data)
        assert len(response.results) == 0
        assert response.total_attributes == 0
        assert response.success_count == 0
        assert response.failed_count == 0

    def test_batch_response_missing_fields(self):
        """Test RoleAttributeMappingBatchResponse with missing required fields"""
        with pytest.raises(ValidationError) as exc_info:
            RoleAttributeMappingBatchResponse(results=[])

        errors = exc_info.value.errors()
        assert len(errors) == 3  # total_attributes, success_count, failed_count missing


class TestPermissionCheckRequest:
    """Test PermissionCheckRequest schema validation"""

    def test_permission_check_request_valid_data(self):
        """Test PermissionCheckRequest with valid data"""
        request_data = {"attributes": ["view-users", "manage-roles", "edit-content"]}

        request = PermissionCheckRequest(**request_data)
        assert len(request.attributes) == 3
        assert "view-users" in request.attributes
        assert "manage-roles" in request.attributes
        assert "edit-content" in request.attributes

    def test_permission_check_request_single_attribute(self):
        """Test PermissionCheckRequest with single attribute"""
        request_data = {"attributes": ["view-users"]}
        request = PermissionCheckRequest(**request_data)
        assert len(request.attributes) == 1
        assert request.attributes[0] == "view-users"

    def test_permission_check_request_empty_attributes(self):
        """Test PermissionCheckRequest with empty attributes list"""
        with pytest.raises(ValidationError) as exc_info:
            PermissionCheckRequest(attributes=[])

        errors = exc_info.value.errors()
        assert any(error["type"] == "too_short" for error in errors)

    def test_permission_check_request_missing_attributes(self):
        """Test PermissionCheckRequest with missing attributes field"""
        # attributes is Optional, so it should be None when not provided
        request = PermissionCheckRequest()
        assert request.attributes is None


class TestPermissionCheckResponse:
    """Test PermissionCheckResponse schema validation"""

    def test_permission_check_response_valid_data(self):
        """Test PermissionCheckResponse with valid data"""
        response_data = {
            "permissions": {
                "view-users": True,
                "manage-roles": False,
                "edit-content": True,
            }
        }

        response = PermissionCheckResponse(**response_data)
        assert response.permissions["view-users"] is True
        assert response.permissions["manage-roles"] is False
        assert response.permissions["edit-content"] is True

    def test_permission_check_response_empty_permissions(self):
        """Test PermissionCheckResponse with empty permissions"""
        response_data = {"permissions": {}}
        response = PermissionCheckResponse(**response_data)
        assert len(response.permissions) == 0

    def test_permission_check_response_missing_permissions(self):
        """Test PermissionCheckResponse with missing permissions field"""
        with pytest.raises(ValidationError) as exc_info:
            PermissionCheckResponse()

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "missing"
        assert errors[0]["loc"] == ("permissions",)