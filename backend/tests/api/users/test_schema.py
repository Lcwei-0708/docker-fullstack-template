import pytest
from datetime import datetime
from pydantic import ValidationError
from api.users.schema import (
    UserResponse,
    UserPagination,
    UserSortBy,
    UserCreate,
    UserUpdate,
    UserDelete,
    PasswordReset,
    UserDeleteResult,
    UserDeleteBatchResponse,
)


class TestUserResponse:
    """Test UserResponse schema validation"""

    def test_user_response_valid_data(self):
        """Test UserResponse with valid data"""
        user_data = {
            "id": "user123",
            "email": "user@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "phone": "+1234567890",
            "status": True,
            "created_at": datetime.now(),
            "role": "admin",
        }

        user = UserResponse(**user_data)

        assert user.id == "user123"
        assert user.email == "user@example.com"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.phone == "+1234567890"
        assert user.status == True
        assert user.role == "admin"

    def test_user_response_without_role(self):
        """Test UserResponse without optional role field"""
        user_data = {
            "id": "user123",
            "email": "user@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "phone": "+1234567890",
            "status": True,
            "created_at": datetime.now(),
        }

        user = UserResponse(**user_data)

        assert user.role is None

    def test_user_response_missing_required_fields(self):
        """Test UserResponse with missing required fields"""
        with pytest.raises(ValidationError) as exc_info:
            UserResponse(
                id="user123",
                email="user@example.com",
                # Missing required fields
            )

        errors = exc_info.value.errors()
        assert len(errors) > 0


class TestUserPagination:
    """Test UserPagination schema validation"""

    def test_user_pagination_valid_data(self):
        """Test UserPagination with valid data"""
        users = [
            UserResponse(
                id="user1",
                email="user1@example.com",
                first_name="User",
                last_name="One",
                phone="+1234567890",
                status=True,
                created_at=datetime.now(),
            ),
            UserResponse(
                id="user2",
                email="user2@example.com",
                first_name="User",
                last_name="Two",
                phone="+1234567891",
                status=True,
                created_at=datetime.now(),
            ),
        ]

        pagination_data = {
            "users": users,
            "total": 2,
            "page": 1,
            "per_page": 10,
            "total_pages": 1,
        }

        pagination = UserPagination(**pagination_data)

        assert len(pagination.users) == 2
        assert pagination.total == 2
        assert pagination.page == 1
        assert pagination.per_page == 10
        assert pagination.total_pages == 1

    def test_user_pagination_empty_users(self):
        """Test UserPagination with empty users list"""
        pagination_data = {
            "users": [],
            "total": 0,
            "page": 1,
            "per_page": 10,
            "total_pages": 0,
        }

        pagination = UserPagination(**pagination_data)

        assert len(pagination.users) == 0
        assert pagination.total == 0
        assert pagination.total_pages == 0


class TestUserSortBy:
    """Test UserSortBy enum validation"""

    def test_user_sort_by_values(self):
        """Test UserSortBy enum values"""
        assert UserSortBy.CREATED_AT == "created_at"
        assert UserSortBy.EMAIL == "email"
        assert UserSortBy.FIRST_NAME == "first_name"
        assert UserSortBy.LAST_NAME == "last_name"
        assert UserSortBy.STATUS == "status"

    def test_user_sort_by_enum_membership(self):
        """Test UserSortBy enum membership"""
        assert "created_at" in UserSortBy.__members__.values()
        assert "email" in UserSortBy.__members__.values()
        assert "first_name" in UserSortBy.__members__.values()
        assert "last_name" in UserSortBy.__members__.values()
        assert "status" in UserSortBy.__members__.values()


class TestUserCreate:
    """Test UserCreate schema validation"""

    def test_user_create_valid_data(self):
        """Test UserCreate with valid data"""
        user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1234567890",
            "password": "TestPassword123!",
            "status": True,
            "role": "admin",
        }

        user = UserCreate(**user_data)

        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.email == "john.doe@example.com"
        assert user.phone == "+1234567890"
        assert user.password == "TestPassword123!"
        assert user.status == True
        assert user.role == "admin"

    def test_user_create_without_optional_fields(self):
        """Test UserCreate without optional fields"""
        user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1234567890",
            "password": "TestPassword123!",
        }

        user = UserCreate(**user_data)

        assert user.status == True  # Default value
        assert user.role is None

    def test_user_create_invalid_email(self):
        """Test UserCreate with invalid email format"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                first_name="John",
                last_name="Doe",
                email="invalid-email",
                phone="+1234567890",
                password="TestPassword123!",
            )

        errors = exc_info.value.errors()
        assert any("email" in str(error) for error in errors)

    def test_user_create_short_password(self):
        """Test UserCreate with password too short"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                first_name="John",
                last_name="Doe",
                email="john.doe@example.com",
                phone="+1234567890",
                password="123",  # Too short
            )

        errors = exc_info.value.errors()
        assert any("password" in str(error) for error in errors)

    def test_user_create_long_first_name(self):
        """Test UserCreate with first name too long"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                first_name="A" * 51,  # Too long
                last_name="Doe",
                email="john.doe@example.com",
                phone="+1234567890",
                password="TestPassword123!",
            )

        errors = exc_info.value.errors()
        assert any("first_name" in str(error) for error in errors)

    def test_user_create_empty_first_name(self):
        """Test UserCreate with empty first name"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                first_name="",  # Empty
                last_name="Doe",
                email="john.doe@example.com",
                phone="+1234567890",
                password="TestPassword123!",
            )

        errors = exc_info.value.errors()
        assert any("first_name" in str(error) for error in errors)

    def test_user_create_long_phone(self):
        """Test UserCreate with phone number too long"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                first_name="John",
                last_name="Doe",
                email="john.doe@example.com",
                phone="+12345678901234567890",  # Too long
                password="TestPassword123!",
            )

        errors = exc_info.value.errors()
        assert any("phone" in str(error) for error in errors)


class TestUserUpdate:
    """Test UserUpdate schema validation"""

    def test_user_update_valid_data(self):
        """Test UserUpdate with valid data"""
        update_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "email": "updated@example.com",
            "phone": "+1234567890",
            "status": False,
            "role": "user",
        }

        user = UserUpdate(**update_data)

        assert user.first_name == "Updated"
        assert user.last_name == "Name"
        assert user.email == "updated@example.com"
        assert user.phone == "+1234567890"
        assert user.status == False
        assert user.role == "user"

    def test_user_update_partial_data(self):
        """Test UserUpdate with partial data"""
        update_data = {"first_name": "Updated"}

        user = UserUpdate(**update_data)

        assert user.first_name == "Updated"
        assert user.last_name is None
        assert user.email is None
        assert user.phone is None
        assert user.status is None
        assert user.role is None

    def test_user_update_empty_data(self):
        """Test UserUpdate with empty data"""
        user = UserUpdate()

        assert user.first_name is None
        assert user.last_name is None
        assert user.email is None
        assert user.phone is None
        assert user.status is None
        assert user.role is None

    def test_user_update_invalid_email(self):
        """Test UserUpdate with invalid email format"""
        with pytest.raises(ValidationError) as exc_info:
            UserUpdate(email="invalid-email")

        errors = exc_info.value.errors()
        assert any("email" in str(error) for error in errors)

    def test_user_update_short_password(self):
        """Test UserUpdate with password too short (if password field exists)"""
        # Note: UserUpdate doesn't have password field, this is just for demonstration
        # of how validation would work if it had one
        pass


class TestUserDelete:
    """Test UserDelete schema validation"""

    def test_user_delete_valid_data(self):
        """Test UserDelete with valid data"""
        delete_data = {"user_ids": ["user1", "user2", "user3"]}

        user_delete = UserDelete(**delete_data)

        assert len(user_delete.user_ids) == 3
        assert "user1" in user_delete.user_ids
        assert "user2" in user_delete.user_ids
        assert "user3" in user_delete.user_ids

    def test_user_delete_single_user(self):
        """Test UserDelete with single user"""
        delete_data = {"user_ids": ["user1"]}

        user_delete = UserDelete(**delete_data)

        assert len(user_delete.user_ids) == 1
        assert user_delete.user_ids[0] == "user1"

    def test_user_delete_empty_list(self):
        """Test UserDelete with empty user list"""
        with pytest.raises(ValidationError) as exc_info:
            UserDelete(user_ids=[])

        errors = exc_info.value.errors()
        assert any("user_ids" in str(error) for error in errors)

    def test_user_delete_missing_field(self):
        """Test UserDelete with missing user_ids field"""
        with pytest.raises(ValidationError) as exc_info:
            UserDelete()

        errors = exc_info.value.errors()
        assert any("user_ids" in str(error) for error in errors)


class TestPasswordReset:
    """Test PasswordReset schema validation"""

    def test_password_reset_valid_data(self):
        """Test PasswordReset with valid data"""
        password_data = {"new_password": "NewPassword123!"}

        password_reset = PasswordReset(**password_data)

        assert password_reset.new_password == "NewPassword123!"

    def test_password_reset_short_password(self):
        """Test PasswordReset with password too short"""
        with pytest.raises(ValidationError) as exc_info:
            PasswordReset(new_password="123")  # Too short

        errors = exc_info.value.errors()
        assert any("new_password" in str(error) for error in errors)

    def test_password_reset_long_password(self):
        """Test PasswordReset with password too long"""
        with pytest.raises(ValidationError) as exc_info:
            PasswordReset(new_password="A" * 51)  # Too long

        errors = exc_info.value.errors()
        assert any("new_password" in str(error) for error in errors)

    def test_password_reset_missing_field(self):
        """Test PasswordReset with missing new_password field"""
        with pytest.raises(ValidationError) as exc_info:
            PasswordReset()

        errors = exc_info.value.errors()
        assert any("new_password" in str(error) for error in errors)


class TestSchemaIntegration:
    """Test schema integration scenarios"""

    def test_user_workflow_schemas(self):
        """Test complete user workflow with different schemas"""
        # 1. Create user
        create_data = UserCreate(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="+1234567890",
            password="TestPassword123!",
            status=True,
            role="admin",
        )

        # 2. Update user
        update_data = UserUpdate(first_name="Updated John", status=False)

        # 3. Delete users
        delete_data = UserDelete(user_ids=["user1", "user2"])

        # 4. Reset password
        password_reset = PasswordReset(new_password="NewPassword123!")

        # 5. Response data
        response_data = UserResponse(
            id="user1",
            email="john.doe@example.com",
            first_name="Updated John",
            last_name="Doe",
            phone="+1234567890",
            status=False,
            created_at=datetime.now(),
            role="admin",
        )

        # 6. Pagination data
        pagination_data = UserPagination(
            users=[response_data], total=1, page=1, per_page=10, total_pages=1
        )

        # All schemas should be valid
        assert create_data.first_name == "John"
        assert update_data.first_name == "Updated John"
        assert len(delete_data.user_ids) == 2
        assert password_reset.new_password == "NewPassword123!"
        assert response_data.email == "john.doe@example.com"
        assert pagination_data.total == 1

    def test_schema_serialization(self):
        """Test schema serialization to dict"""
        user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1234567890",
            "password": "TestPassword123!",
            "status": True,
            "role": "admin",
        }

        user = UserCreate(**user_data)
        serialized = user.model_dump()

        assert serialized["first_name"] == "John"
        assert serialized["last_name"] == "Doe"
        assert serialized["email"] == "john.doe@example.com"
        assert serialized["phone"] == "+1234567890"
        assert serialized["password"] == "TestPassword123!"
        assert serialized["status"] == True
        assert serialized["role"] == "admin"

    def test_schema_exclude_unset(self):
        """Test schema exclude_unset functionality"""
        user = UserUpdate(first_name="Updated")
        serialized = user.model_dump(exclude_unset=True)

        assert "first_name" in serialized
        assert "last_name" not in serialized
        assert "email" not in serialized
        assert "phone" not in serialized
        assert "status" not in serialized
        assert "role" not in serialized


class TestUserDeleteResult:
    """Test UserDeleteResult schema validation"""

    def test_user_delete_result_success(self):
        """Test UserDeleteResult with success status"""
        result_data = {
            "user_id": "user123",
            "status": "success",
            "message": "User deleted successfully"
        }

        result = UserDeleteResult(**result_data)

        assert result.user_id == "user123"
        assert result.status == "success"
        assert result.message == "User deleted successfully"

    def test_user_delete_result_failed(self):
        """Test UserDeleteResult with failed status"""
        result_data = {
            "user_id": "user456",
            "status": "failed",
            "message": "User not found"
        }

        result = UserDeleteResult(**result_data)

        assert result.user_id == "user456"
        assert result.status == "failed"
        assert result.message == "User not found"

    def test_user_delete_result_missing_fields(self):
        """Test UserDeleteResult with missing required fields"""
        with pytest.raises(ValidationError) as exc_info:
            UserDeleteResult(
                user_id="user123",
                # Missing status and message
            )

        errors = exc_info.value.errors()
        assert len(errors) > 0

    def test_user_delete_result_invalid_status(self):
        """Test UserDeleteResult with invalid status"""
        with pytest.raises(ValidationError) as exc_info:
            UserDeleteResult(
                user_id="user123",
                status="invalid_status",
                message="Test message"
            )

        errors = exc_info.value.errors()
        assert any("status" in str(error) for error in errors)


class TestUserDeleteBatchResponse:
    """Test UserDeleteBatchResponse schema validation"""

    def test_user_delete_batch_response_success(self):
        """Test UserDeleteBatchResponse with all successful deletions"""
        results = [
            UserDeleteResult(
                user_id="user1",
                status="success",
                message="User deleted successfully"
            ),
            UserDeleteResult(
                user_id="user2",
                status="success",
                message="User deleted successfully"
            )
        ]

        batch_data = {
            "results": results,
            "total_users": 2,
            "success_count": 2,
            "failed_count": 0
        }

        batch_response = UserDeleteBatchResponse(**batch_data)

        assert len(batch_response.results) == 2
        assert batch_response.total_users == 2
        assert batch_response.success_count == 2
        assert batch_response.failed_count == 0
        assert all(r.status == "success" for r in batch_response.results)

    def test_user_delete_batch_response_partial_success(self):
        """Test UserDeleteBatchResponse with partial success"""
        results = [
            UserDeleteResult(
                user_id="user1",
                status="success",
                message="User deleted successfully"
            ),
            UserDeleteResult(
                user_id="user2",
                status="failed",
                message="User not found"
            )
        ]

        batch_data = {
            "results": results,
            "total_users": 2,
            "success_count": 1,
            "failed_count": 1
        }

        batch_response = UserDeleteBatchResponse(**batch_data)

        assert len(batch_response.results) == 2
        assert batch_response.total_users == 2
        assert batch_response.success_count == 1
        assert batch_response.failed_count == 1

    def test_user_delete_batch_response_all_failed(self):
        """Test UserDeleteBatchResponse with all failed deletions"""
        results = [
            UserDeleteResult(
                user_id="user1",
                status="failed",
                message="User not found"
            ),
            UserDeleteResult(
                user_id="user2",
                status="failed",
                message="User not found"
            )
        ]

        batch_data = {
            "results": results,
            "total_users": 2,
            "success_count": 0,
            "failed_count": 2
        }

        batch_response = UserDeleteBatchResponse(**batch_data)

        assert len(batch_response.results) == 2
        assert batch_response.total_users == 2
        assert batch_response.success_count == 0
        assert batch_response.failed_count == 2
        assert all(r.status == "failed" for r in batch_response.results)

    def test_user_delete_batch_response_empty_results(self):
        """Test UserDeleteBatchResponse with empty results"""
        batch_data = {
            "results": [],
            "total_users": 0,
            "success_count": 0,
            "failed_count": 0
        }

        batch_response = UserDeleteBatchResponse(**batch_data)

        assert len(batch_response.results) == 0
        assert batch_response.total_users == 0
        assert batch_response.success_count == 0
        assert batch_response.failed_count == 0

    def test_user_delete_batch_response_missing_fields(self):
        """Test UserDeleteBatchResponse with missing required fields"""
        with pytest.raises(ValidationError) as exc_info:
            UserDeleteBatchResponse(
                results=[],
                # Missing total_users, success_count, failed_count
            )

        errors = exc_info.value.errors()
        assert len(errors) > 0

    def test_user_delete_batch_response_serialization(self):
        """Test UserDeleteBatchResponse serialization"""
        results = [
            UserDeleteResult(
                user_id="user1",
                status="success",
                message="User deleted successfully"
            )
        ]

        batch_data = {
            "results": results,
            "total_users": 1,
            "success_count": 1,
            "failed_count": 0
        }

        batch_response = UserDeleteBatchResponse(**batch_data)
        serialized = batch_response.model_dump()

        assert "results" in serialized
        assert "total_users" in serialized
        assert "success_count" in serialized
        assert "failed_count" in serialized
        assert len(serialized["results"]) == 1
        assert serialized["total_users"] == 1
        assert serialized["success_count"] == 1
        assert serialized["failed_count"] == 0


class TestBatchDeleteIntegration:
    """Test batch delete integration scenarios"""

    def test_batch_delete_workflow(self):
        """Test complete batch delete workflow with different scenarios"""
        # 1. Create batch response with mixed results
        results = [
            UserDeleteResult(
                user_id="user1",
                status="success",
                message="User deleted successfully"
            ),
            UserDeleteResult(
                user_id="user2",
                status="failed",
                message="User not found"
            ),
            UserDeleteResult(
                user_id="user3",
                status="success",
                message="User deleted successfully"
            )
        ]

        batch_response = UserDeleteBatchResponse(
            results=results,
            total_users=3,
            success_count=2,
            failed_count=1
        )

        # 2. Verify response structure
        assert batch_response.total_users == 3
        assert batch_response.success_count == 2
        assert batch_response.failed_count == 1
        assert len(batch_response.results) == 3

        # 3. Verify individual results
        success_results = [r for r in batch_response.results if r.status == "success"]
        failed_results = [r for r in batch_response.results if r.status == "failed"]

        assert len(success_results) == 2
        assert len(failed_results) == 1
        assert success_results[0].user_id == "user1"
        assert success_results[1].user_id == "user3"
        assert failed_results[0].user_id == "user2"

        # 4. Test serialization
        serialized = batch_response.model_dump()
        assert serialized["total_users"] == 3
        assert serialized["success_count"] == 2
        assert serialized["failed_count"] == 1

    def test_batch_delete_response_codes(self):
        """Test batch delete response codes based on results"""
        # All successful
        all_success = UserDeleteBatchResponse(
            results=[
                UserDeleteResult(user_id="user1", status="success", message="Success"),
                UserDeleteResult(user_id="user2", status="success", message="Success")
            ],
            total_users=2,
            success_count=2,
            failed_count=0
        )
        assert all_success.failed_count == 0  # Should return 200

        # Partial success
        partial_success = UserDeleteBatchResponse(
            results=[
                UserDeleteResult(user_id="user1", status="success", message="Success"),
                UserDeleteResult(user_id="user2", status="failed", message="Failed")
            ],
            total_users=2,
            success_count=1,
            failed_count=1
        )
        assert partial_success.success_count > 0 and partial_success.failed_count > 0  # Should return 207

        # All failed
        all_failed = UserDeleteBatchResponse(
            results=[
                UserDeleteResult(user_id="user1", status="failed", message="Failed"),
                UserDeleteResult(user_id="user2", status="failed", message="Failed")
            ],
            total_users=2,
            success_count=0,
            failed_count=2
        )
        assert all_failed.success_count == 0  # Should return 400