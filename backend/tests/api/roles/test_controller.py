import pytest
from unittest.mock import patch
from httpx import AsyncClient
from api.roles.schema import (
    RoleResponse,
    RolesListResponse,
    RoleAttributesMapping,
    RoleAttributeMappingBatchResponse,
    AttributeMappingResult,
    PermissionCheckResponse,
)
from utils.custom_exception import ConflictException, NotFoundException, ServerException


class TestGetRolesAPI:
    """Test GET /api/roles/ endpoint"""

    @pytest.mark.asyncio
    async def test_get_roles_success(
        self, client: AsyncClient, users_auth_headers: dict
    ):
        """Test successful roles retrieval with valid authentication"""
        with patch("api.roles.controller.get_all_roles") as mock_get_roles:
            mock_roles = RolesListResponse(
                roles=[
                    RoleResponse(id="role-1", name="admin", description="Admin role"),
                    RoleResponse(id="role-2", name="user", description="User role"),
                ]
            )
            mock_get_roles.return_value = mock_roles

            response = await client.get(
                "/api/roles/",
                headers={"Authorization": users_auth_headers["Authorization"]},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["message"] == "Successfully retrieved roles"
            assert "data" in data
            assert "roles" in data["data"]
            assert len(data["data"]["roles"]) == 2

    @pytest.mark.asyncio
    async def test_get_roles_unauthorized(self, client: AsyncClient):
        """Test roles access without authentication token"""
        response = await client.get("/api/roles/")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_roles_server_error(
        self, client: AsyncClient, users_auth_headers: dict
    ):
        """Test roles retrieval with server error"""
        with patch(
            "api.roles.controller.get_all_roles",
            side_effect=Exception("Database error"),
        ):
            response = await client.get(
                "/api/roles/",
                headers={"Authorization": users_auth_headers["Authorization"]},
            )
            assert response.status_code == 500


class TestCreateRoleAPI:
    """Test POST /api/roles/ endpoint"""

    @pytest.mark.asyncio
    async def test_create_role_success(
        self, client: AsyncClient, users_auth_headers: dict
    ):
        """Test successful role creation"""
        role_data = {
            "name": "manager",
            "description": "Manager role with special permissions",
        }

        with patch("api.roles.controller.create_role") as mock_create_role:
            mock_role = RoleResponse(
                id="role-123",
                name="manager",
                description="Manager role with special permissions",
            )
            mock_create_role.return_value = mock_role

            response = await client.post(
                "/api/roles/",
                json=role_data,
                headers={"Authorization": users_auth_headers["Authorization"]},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["message"] == "Role created successfully"
            assert data["data"]["name"] == "manager"

    @pytest.mark.asyncio
    async def test_create_role_conflict(
        self, client: AsyncClient, users_auth_headers: dict
    ):
        """Test role creation with name conflict"""
        role_data = {"name": "admin", "description": "Admin role"}

        with patch("api.roles.controller.create_role") as mock_create_role:
            mock_create_role.side_effect = ConflictException("Role name already exists")

            response = await client.post(
                "/api/roles/",
                json=role_data,
                headers={"Authorization": users_auth_headers["Authorization"]},
            )

            assert response.status_code == 409
            data = response.json()
            assert data["code"] == 409
            assert data["message"] == "Role name already exists"

    @pytest.mark.asyncio
    async def test_create_role_unauthorized(self, client: AsyncClient):
        """Test role creation without authentication"""
        role_data = {"name": "test-role"}
        response = await client.post("/api/roles/", json=role_data)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_role_server_error(
        self, client: AsyncClient, users_auth_headers: dict
    ):
        """Test role creation with server error"""
        role_data = {"name": "test-role"}

        with patch(
            "api.roles.controller.create_role", side_effect=Exception("Database error")
        ):
            response = await client.post(
                "/api/roles/",
                json=role_data,
                headers={"Authorization": users_auth_headers["Authorization"]},
            )
            assert response.status_code == 500


class TestUpdateRoleAPI:
    """Test PUT /api/roles/{role_id} endpoint"""

    @pytest.mark.asyncio
    async def test_update_role_success(
        self, client: AsyncClient, users_auth_headers: dict
    ):
        """Test successful role update"""
        role_id = "role-123"
        role_data = {"name": "updated_manager", "description": "Updated manager role"}

        with patch("api.roles.controller.update_role") as mock_update_role:
            mock_role = RoleResponse(
                id=role_id, name="updated_manager", description="Updated manager role"
            )
            mock_update_role.return_value = mock_role

            response = await client.put(
                f"/api/roles/{role_id}",
                json=role_data,
                headers={"Authorization": users_auth_headers["Authorization"]},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["message"] == "Role updated successfully"
            assert data["data"]["name"] == "updated_manager"

    @pytest.mark.asyncio
    async def test_update_role_not_found(
        self, client: AsyncClient, users_auth_headers: dict
    ):
        """Test role update with non-existent role"""
        role_id = "non-existent-role"
        role_data = {"name": "updated_role"}

        with patch("api.roles.controller.update_role") as mock_update_role:
            mock_update_role.side_effect = NotFoundException("Role not found")

            response = await client.put(
                f"/api/roles/{role_id}",
                json=role_data,
                headers={"Authorization": users_auth_headers["Authorization"]},
            )

            assert response.status_code == 404
            data = response.json()
            assert data["code"] == 404
            assert data["message"] == "Role not found"

    @pytest.mark.asyncio
    async def test_update_role_conflict(
        self, client: AsyncClient, users_auth_headers: dict
    ):
        """Test role update with name conflict"""
        role_id = "role-123"
        role_data = {"name": "existing-role"}

        with patch("api.roles.controller.update_role") as mock_update_role:
            mock_update_role.side_effect = ConflictException("Role name already exists")

            response = await client.put(
                f"/api/roles/{role_id}",
                json=role_data,
                headers={"Authorization": users_auth_headers["Authorization"]},
            )

            assert response.status_code == 409
            data = response.json()
            assert data["code"] == 409
            assert data["message"] == "Role name already exists"

    @pytest.mark.asyncio
    async def test_update_role_unauthorized(self, client: AsyncClient):
        """Test role update without authentication"""
        role_id = "role-123"
        role_data = {"name": "updated_role"}
        response = await client.put(f"/api/roles/{role_id}", json=role_data)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_role_server_error(
        self, client: AsyncClient, users_auth_headers: dict
    ):
        """Test role update with server error"""
        role_id = "role-123"
        role_data = {"name": "updated_role"}

        with patch(
            "api.roles.controller.update_role",
            side_effect=ServerException("Database error"),
        ):
            response = await client.put(
                f"/api/roles/{role_id}",
                json=role_data,
                headers={"Authorization": users_auth_headers["Authorization"]},
            )
            assert response.status_code == 500


class TestDeleteRoleAPI:
    """Test DELETE /api/roles/{role_id} endpoint"""

    @pytest.mark.asyncio
    async def test_delete_role_success(
        self, client: AsyncClient, users_auth_headers: dict
    ):
        """Test successful role deletion"""
        role_id = "role-123"

        with patch("api.roles.controller.delete_role") as mock_delete_role:
            mock_delete_role.return_value = True

            response = await client.delete(
                f"/api/roles/{role_id}",
                headers={"Authorization": users_auth_headers["Authorization"]},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["message"] == "Role deleted successfully"

    @pytest.mark.asyncio
    async def test_delete_role_not_found(
        self, client: AsyncClient, users_auth_headers: dict
    ):
        """Test role deletion with non-existent role"""
        role_id = "non-existent-role"

        with patch("api.roles.controller.delete_role") as mock_delete_role:
            mock_delete_role.side_effect = NotFoundException("Role not found")

            response = await client.delete(
                f"/api/roles/{role_id}",
                headers={"Authorization": users_auth_headers["Authorization"]},
            )

            assert response.status_code == 404
            data = response.json()
            assert data["code"] == 404
            assert data["message"] == "Role not found"

    @pytest.mark.asyncio
    async def test_delete_role_conflict(
        self, client: AsyncClient, users_auth_headers: dict
    ):
        """Test role deletion when role is assigned to users"""
        role_id = "role-123"

        with patch("api.roles.controller.delete_role") as mock_delete_role:
            mock_delete_role.side_effect = ConflictException(
                "Cannot delete role that is assigned to users"
            )

            response = await client.delete(
                f"/api/roles/{role_id}",
                headers={"Authorization": users_auth_headers["Authorization"]},
            )

            assert response.status_code == 409
            data = response.json()
            assert data["code"] == 409
            assert data["message"] == "Cannot delete role that is assigned to users"

    @pytest.mark.asyncio
    async def test_delete_role_unauthorized(self, client: AsyncClient):
        """Test role deletion without authentication"""
        role_id = "role-123"
        response = await client.delete(f"/api/roles/{role_id}")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_role_server_error(
        self, client: AsyncClient, users_auth_headers: dict
    ):
        """Test role deletion with server error"""
        role_id = "role-123"

        with patch(
            "api.roles.controller.delete_role", side_effect=Exception("Database error")
        ):
            response = await client.delete(
                f"/api/roles/{role_id}",
                headers={"Authorization": users_auth_headers["Authorization"]},
            )
            assert response.status_code == 500


class TestGetRoleAttributeMappingAPI:
    """Test GET /api/roles/{role_id}/attributes endpoint"""

    @pytest.mark.asyncio
    async def test_get_role_attribute_mapping_success(
        self, client: AsyncClient, users_auth_headers: dict
    ):
        """Test successful role attributes mapping retrieval"""
        role_id = "role-123"

        with patch(
            "api.roles.controller.get_role_attribute_mapping"
        ) as mock_get_mapping:
            mock_mapping = RoleAttributesMapping(
                attributes={"attr-1": True, "attr-2": False, "attr-3": True}
            )
            mock_get_mapping.return_value = mock_mapping

            response = await client.get(
                f"/api/roles/{role_id}/attributes",
                headers={"Authorization": users_auth_headers["Authorization"]},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["message"] == "Successfully retrieved role attributes mapping"
            assert "data" in data
            assert "attributes" in data["data"]
            assert data["data"]["attributes"]["attr-1"] is True
            assert data["data"]["attributes"]["attr-2"] is False

    @pytest.mark.asyncio
    async def test_get_role_attribute_mapping_not_found(
        self, client: AsyncClient, users_auth_headers: dict
    ):
        """Test role attributes mapping retrieval with non-existent role"""
        role_id = "non-existent-role"

        with patch(
            "api.roles.controller.get_role_attribute_mapping"
        ) as mock_get_mapping:
            mock_get_mapping.side_effect = NotFoundException("Role not found")

            response = await client.get(
                f"/api/roles/{role_id}/attributes",
                headers={"Authorization": users_auth_headers["Authorization"]},
            )

            assert response.status_code == 404
            data = response.json()
            assert data["code"] == 404
            assert data["message"] == "Role not found"

    @pytest.mark.asyncio
    async def test_get_role_attribute_mapping_unauthorized(self, client: AsyncClient):
        """Test role attributes mapping retrieval without authentication"""
        role_id = "role-123"
        response = await client.get(f"/api/roles/{role_id}/attributes")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_role_attribute_mapping_server_error(
        self, client: AsyncClient, users_auth_headers: dict
    ):
        """Test role attributes mapping retrieval with server error"""
        role_id = "role-123"

        with patch(
            "api.roles.controller.get_role_attribute_mapping",
            side_effect=Exception("Database error"),
        ):
            response = await client.get(
                f"/api/roles/{role_id}/attributes",
                headers={"Authorization": users_auth_headers["Authorization"]},
            )
            assert response.status_code == 500


class TestUpdateRoleAttributeMappingAPI:
    """Test PUT /api/roles/{role_id}/attributes endpoint"""

    @pytest.mark.asyncio
    async def test_update_role_attribute_mapping_success(
        self, client: AsyncClient, users_auth_headers: dict
    ):
        """Test successful role attributes mapping update"""
        role_id = "role-123"
        attributes_data = {"attributes": {"attr-1": True, "attr-2": False}}

        with patch(
            "api.roles.controller.update_role_attribute_mapping"
        ) as mock_update_mapping:
            mock_batch_result = RoleAttributeMappingBatchResponse(
                results=[
                    AttributeMappingResult(
                        attribute_id="attr-1",
                        status="success",
                        message="Updated successfully",
                    ),
                    AttributeMappingResult(
                        attribute_id="attr-2",
                        status="success",
                        message="Updated successfully",
                    ),
                ],
                total_attributes=2,
                success_count=2,
                failed_count=0,
            )
            mock_update_mapping.return_value = mock_batch_result

            response = await client.put(
                f"/api/roles/{role_id}/attributes",
                json=attributes_data,
                headers={"Authorization": users_auth_headers["Authorization"]},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["message"] == "All role attributes processed successfully"
            assert data["data"]["success_count"] == 2
            assert data["data"]["failed_count"] == 0

    @pytest.mark.asyncio
    async def test_update_role_attribute_mapping_partial_success(
        self, client: AsyncClient, users_auth_headers: dict
    ):
        """Test role attributes mapping update with partial success"""
        role_id = "role-123"
        attributes_data = {"attributes": {"attr-1": True, "invalid-attr": False}}

        with patch(
            "api.roles.controller.update_role_attribute_mapping"
        ) as mock_update_mapping:
            mock_batch_result = RoleAttributeMappingBatchResponse(
                results=[
                    AttributeMappingResult(
                        attribute_id="attr-1",
                        status="success",
                        message="Updated successfully",
                    ),
                    AttributeMappingResult(
                        attribute_id="invalid-attr",
                        status="failed",
                        message="Invalid attribute ID",
                    ),
                ],
                total_attributes=2,
                success_count=1,
                failed_count=1,
            )
            mock_update_mapping.return_value = mock_batch_result

            response = await client.put(
                f"/api/roles/{role_id}/attributes",
                json=attributes_data,
                headers={"Authorization": users_auth_headers["Authorization"]},
            )

            assert response.status_code == 207  # Partial success should return 207
            data = response.json()
            assert data["code"] == 207
            assert data["message"] == "Role attributes processed with partial success"
            assert data["data"]["success_count"] == 1
            assert data["data"]["failed_count"] == 1

    @pytest.mark.asyncio
    async def test_update_role_attribute_mapping_all_failed(
        self, client: AsyncClient, users_auth_headers: dict
    ):
        """Test role attributes mapping update with all failures"""
        role_id = "role-123"
        attributes_data = {
            "attributes": {"invalid-attr-1": True, "invalid-attr-2": False}
        }

        with patch(
            "api.roles.controller.update_role_attribute_mapping"
        ) as mock_update_mapping:
            mock_batch_result = RoleAttributeMappingBatchResponse(
                results=[
                    AttributeMappingResult(
                        attribute_id="invalid-attr-1",
                        status="failed",
                        message="Invalid attribute ID",
                    ),
                    AttributeMappingResult(
                        attribute_id="invalid-attr-2",
                        status="failed",
                        message="Invalid attribute ID",
                    ),
                ],
                total_attributes=2,
                success_count=0,
                failed_count=2,
            )
            mock_update_mapping.return_value = mock_batch_result

            response = await client.put(
                f"/api/roles/{role_id}/attributes",
                json=attributes_data,
                headers={"Authorization": users_auth_headers["Authorization"]},
            )

            assert response.status_code == 400  # All failed should return 400
            data = response.json()
            assert data["code"] == 400
            assert data["message"] == "All role attributes failed to process"
            assert data["data"]["success_count"] == 0
            assert data["data"]["failed_count"] == 2

    @pytest.mark.asyncio
    async def test_update_role_attribute_mapping_not_found(
        self, client: AsyncClient, users_auth_headers: dict
    ):
        """Test role attributes mapping update with non-existent role"""
        role_id = "non-existent-role"
        attributes_data = {"attributes": {"attr-1": True}}

        with patch(
            "api.roles.controller.update_role_attribute_mapping"
        ) as mock_update_mapping:
            mock_update_mapping.side_effect = NotFoundException("Role not found")

            response = await client.put(
                f"/api/roles/{role_id}/attributes",
                json=attributes_data,
                headers={"Authorization": users_auth_headers["Authorization"]},
            )

            assert response.status_code == 404
            data = response.json()
            assert data["code"] == 404
            assert data["message"] == "Role not found"

    @pytest.mark.asyncio
    async def test_update_role_attribute_mapping_unauthorized(
        self, client: AsyncClient
    ):
        """Test role attributes mapping update without authentication"""
        role_id = "role-123"
        attributes_data = {"attributes": {"attr-1": True}}
        response = await client.put(
            f"/api/roles/{role_id}/attributes", json=attributes_data
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_role_attribute_mapping_server_error(
        self, client: AsyncClient, users_auth_headers: dict
    ):
        """Test role attributes mapping update with server error"""
        role_id = "role-123"
        attributes_data = {"attributes": {"attr-1": True}}

        with patch(
            "api.roles.controller.update_role_attribute_mapping",
            side_effect=Exception("Database error"),
        ):
            response = await client.put(
                f"/api/roles/{role_id}/attributes",
                json=attributes_data,
                headers={"Authorization": users_auth_headers["Authorization"]},
            )
            assert response.status_code == 500


class TestGetUserPermissionsAPI:
    """Test GET /api/roles/permissions endpoint"""

    @pytest.mark.asyncio
    async def test_get_user_permissions_success(
        self, client: AsyncClient, users_auth_headers: dict
    ):
        """Test successful user permissions retrieval"""
        with patch(
            "api.roles.controller.check_user_permissions"
        ) as mock_check_permissions:
            mock_result = PermissionCheckResponse(
                permissions={
                    "view-users": True,
                    "manage-roles": False,
                    "edit-content": True,
                }
            )
            mock_check_permissions.return_value = mock_result

            response = await client.get(
                "/api/roles/permissions",
                headers={"Authorization": users_auth_headers["Authorization"]},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["message"] == "User permissions retrieved"
            assert data["data"]["permissions"]["view-users"] is True
            assert data["data"]["permissions"]["manage-roles"] is False
            assert data["data"]["permissions"]["edit-content"] is True

    @pytest.mark.asyncio
    async def test_get_user_permissions_unauthorized(self, client: AsyncClient):
        """Test user permissions retrieval without authentication"""
        response = await client.get("/api/roles/permissions")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_user_permissions_server_error(
        self, client: AsyncClient, users_auth_headers: dict
    ):
        """Test user permissions retrieval with server error"""
        with patch(
            "api.roles.controller.check_user_permissions",
            side_effect=Exception("Database error"),
        ):
            response = await client.get(
                "/api/roles/permissions",
                headers={"Authorization": users_auth_headers["Authorization"]},
            )
            assert response.status_code == 500