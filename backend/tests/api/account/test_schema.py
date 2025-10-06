import pytest
from datetime import datetime
from core.config import settings
from pydantic import ValidationError
from api.account.schema import UserProfile, UserUpdate, PasswordChange


class TestUserProfile:
    """Test UserProfile schema validation"""

    def test_valid_user_profile(self):
        """Test valid UserProfile creation with all required fields"""
        valid_data = {
            "id": "test-user-id-123",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1234567890",
            "status": True,
            "created_at": datetime.now(),
        }

        profile = UserProfile(**valid_data)

        assert profile.id == "test-user-id-123"
        assert profile.first_name == "John"
        assert profile.last_name == "Doe"
        assert profile.email == "john.doe@example.com"
        assert profile.phone == "+1234567890"
        assert profile.status is True
        assert isinstance(profile.created_at, datetime)

    def test_user_profile_missing_required_fields(self):
        """Test UserProfile validation with missing required fields"""
        incomplete_data = {
            "id": "test-user-id-123",
            "first_name": "John",
            # Missing last_name, email, phone, status, created_at
        }

        with pytest.raises(ValidationError) as exc_info:
            UserProfile(**incomplete_data)

        errors = exc_info.value.errors()
        assert len(errors) >= 5  # Should have multiple missing field errors

    def test_user_profile_invalid_email(self):
        """Test UserProfile validation with invalid email format"""
        invalid_data = {
            "id": "test-user-id-123",
            "first_name": "John",
            "last_name": "Doe",
            "email": "invalid-email-format",  # Invalid email
            "phone": "+1234567890",
            "status": True,
            "created_at": datetime.now(),
        }

        with pytest.raises(ValidationError) as exc_info:
            UserProfile(**invalid_data)

        errors = exc_info.value.errors()
        assert any(error["type"] == "value_error" for error in errors)

    def test_user_profile_boolean_status(self):
        """Test UserProfile status field accepts boolean values"""
        # Test with True
        profile_true = UserProfile(
            id="test-id",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="+1234567890",
            status=True,
            created_at=datetime.now(),
        )
        assert profile_true.status is True

        # Test with False
        profile_false = UserProfile(
            id="test-id",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="+1234567890",
            status=False,
            created_at=datetime.now(),
        )
        assert profile_false.status is False


class TestUserUpdate:
    """Test UserUpdate schema validation"""

    def test_valid_user_update_all_fields(self):
        """Test valid UserUpdate with all fields provided"""
        valid_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "email": "updated@example.com",
            "phone": "+9876543210",
        }

        update = UserUpdate(**valid_data)

        assert update.first_name == "Updated"
        assert update.last_name == "Name"
        assert update.email == "updated@example.com"
        assert update.phone == "+9876543210"

    def test_valid_user_update_partial_fields(self):
        """Test valid UserUpdate with only some fields provided"""
        partial_data = {"first_name": "PartialUpdate"}

        update = UserUpdate(**partial_data)

        assert update.first_name == "PartialUpdate"
        assert update.last_name is None
        assert update.email is None
        assert update.phone is None

    def test_user_update_empty_dict(self):
        """Test UserUpdate with empty dictionary (all fields optional)"""
        update = UserUpdate()

        assert update.first_name is None
        assert update.last_name is None
        assert update.email is None
        assert update.phone is None

    def test_user_update_invalid_email(self):
        """Test UserUpdate validation with invalid email format"""
        invalid_data = {"first_name": "John", "email": "invalid-email-format"}

        with pytest.raises(ValidationError) as exc_info:
            UserUpdate(**invalid_data)

        errors = exc_info.value.errors()
        assert any(error["type"] == "value_error" for error in errors)

    def test_user_update_string_length_constraints(self):
        """Test UserUpdate field length constraints"""
        # Test first_name too short
        with pytest.raises(ValidationError) as exc_info:
            UserUpdate(first_name="")  # Empty string should fail min_length=1

        errors = exc_info.value.errors()
        assert any("min_length" in str(error) for error in errors)

        # Test first_name too long
        long_name = "a" * 51  # Exceeds max_length=50
        with pytest.raises(ValidationError) as exc_info:
            UserUpdate(first_name=long_name)

        errors = exc_info.value.errors()
        assert any("max_length" in str(error) for error in errors)

    def test_user_update_phone_length_constraints(self):
        """Test UserUpdate phone field length constraints"""
        # Test phone too short
        with pytest.raises(ValidationError) as exc_info:
            UserUpdate(phone="")  # Empty string should fail min_length=1

        errors = exc_info.value.errors()
        assert any("min_length" in str(error) for error in errors)

        # Test phone too long
        long_phone = "1" * 21  # Exceeds max_length=20
        with pytest.raises(ValidationError) as exc_info:
            UserUpdate(phone=long_phone)

        errors = exc_info.value.errors()
        assert any("max_length" in str(error) for error in errors)


class TestPasswordChange:
    """Test PasswordChange schema validation"""

    def test_valid_password_change(self):
        """Test valid PasswordChange with all fields"""
        valid_data = {
            "current_password": "CurrentPass123!",
            "new_password": "NewPass123!",
            "logout_all_devices": True,
        }

        password_change = PasswordChange(**valid_data)

        assert password_change.current_password == "CurrentPass123!"
        assert password_change.new_password == "NewPass123!"
        assert password_change.logout_all_devices is True

    def test_password_change_default_logout_all_devices(self):
        """Test PasswordChange default value for logout_all_devices"""
        data = {"current_password": "CurrentPass123!", "new_password": "NewPass123!"}

        password_change = PasswordChange(**data)

        assert password_change.current_password == "CurrentPass123!"
        assert password_change.new_password == "NewPass123!"
        assert password_change.logout_all_devices is True  # Default value

    def test_password_change_missing_required_fields(self):
        """Test PasswordChange validation with missing required fields"""
        # Missing new_password
        with pytest.raises(ValidationError) as exc_info:
            PasswordChange(current_password="CurrentPass123!")

        errors = exc_info.value.errors()
        assert any("new_password" in str(error) for error in errors)

        # Missing current_password
        with pytest.raises(ValidationError) as exc_info:
            PasswordChange(new_password="NewPass123!")

        errors = exc_info.value.errors()
        assert any("current_password" in str(error) for error in errors)

    def test_password_change_length_constraints(self):
        """Test PasswordChange password length constraints"""
        # Test password too short
        short_password = "a" * (settings.PASSWORD_MIN_LENGTH - 1)

        with pytest.raises(ValidationError) as exc_info:
            PasswordChange(current_password=short_password, new_password="NewPass123!")

        errors = exc_info.value.errors()
        assert any("min_length" in str(error) for error in errors)

        # Test password too long
        long_password = "a" * 51  # Exceeds max_length=50

        with pytest.raises(ValidationError) as exc_info:
            PasswordChange(
                current_password="CurrentPass123!", new_password=long_password
            )

        errors = exc_info.value.errors()
        assert any("max_length" in str(error) for error in errors)

    def test_password_change_boolean_logout_all_devices(self):
        """Test PasswordChange logout_all_devices field accepts boolean values"""
        # Test with True
        password_change_true = PasswordChange(
            current_password="CurrentPass123!",
            new_password="NewPass123!",
            logout_all_devices=True,
        )
        assert password_change_true.logout_all_devices is True

        # Test with False
        password_change_false = PasswordChange(
            current_password="CurrentPass123!",
            new_password="NewPass123!",
            logout_all_devices=False,
        )
        assert password_change_false.logout_all_devices is False


class TestSchemaIntegration:
    """Test schema integration and edge cases"""

    def test_user_update_model_dump_exclude_unset(self):
        """Test UserUpdate model_dump with exclude_unset parameter"""
        # Create with only some fields set
        update = UserUpdate(first_name="John", email="john@example.com")

        # Test model_dump with exclude_unset=True (should only include set fields)
        dumped = update.model_dump(exclude_unset=True)
        expected_keys = {"first_name", "email"}
        assert set(dumped.keys()) == expected_keys
        assert dumped["first_name"] == "John"
        assert dumped["email"] == "john@example.com"

        # Test model_dump with exclude_unset=False (should include all fields)
        dumped_all = update.model_dump(exclude_unset=False)
        expected_all_keys = {"first_name", "last_name", "email", "phone"}
        assert set(dumped_all.keys()) == expected_all_keys
        assert dumped_all["first_name"] == "John"
        assert dumped_all["email"] == "john@example.com"
        assert dumped_all["last_name"] is None
        assert dumped_all["phone"] is None

    def test_schema_field_descriptions(self):
        """Test that schema fields have proper descriptions"""
        # Check UserUpdate field descriptions
        user_update_fields = UserUpdate.model_fields

        assert user_update_fields["first_name"].description is not None
        assert user_update_fields["last_name"].description is not None
        assert user_update_fields["email"].description is not None
        assert user_update_fields["phone"].description is not None

        # Check PasswordChange field descriptions
        password_change_fields = PasswordChange.model_fields

        assert password_change_fields["current_password"].description is not None
        assert password_change_fields["new_password"].description is not None
        assert password_change_fields["logout_all_devices"].description is not None

    def test_schema_validation_error_details(self):
        """Test that validation errors provide detailed information"""
        with pytest.raises(ValidationError) as exc_info:
            UserUpdate(
                first_name="",  # Too short
                email="invalid-email",  # Invalid format
                phone="1" * 25,  # Too long
            )

        errors = exc_info.value.errors()
        error_types = [error["type"] for error in errors]

        # Should have multiple validation errors
        assert len(errors) >= 2
        assert "value_error" in error_types or "string_too_short" in error_types
        assert "value_error" in error_types or "string_too_long" in error_types
