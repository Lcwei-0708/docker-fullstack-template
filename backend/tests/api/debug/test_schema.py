import pytest
from pydantic import ValidationError
from api.debug.schema import IPDebugResponse, ClearBlockedIPsResponse


class TestIPDebugResponse:
    """Test IPDebugResponse schema validation"""

    def test_valid_ip_debug_response_all_fields(self):
        """Test valid IPDebugResponse creation with all fields"""
        valid_data = {
            "client_host": "192.168.1.1",
            "x_forwarded_for": "203.0.113.1, 70.41.3.18, 150.172.238.178",
            "x_real_ip": "203.0.113.1",
            "detected_real_ip": "203.0.113.1",
        }

        response = IPDebugResponse(**valid_data)

        assert response.client_host == "192.168.1.1"
        assert response.x_forwarded_for == "203.0.113.1, 70.41.3.18, 150.172.238.178"
        assert response.x_real_ip == "203.0.113.1"
        assert response.detected_real_ip == "203.0.113.1"

    def test_valid_ip_debug_response_none_values(self):
        """Test valid IPDebugResponse creation with None values"""
        valid_data = {
            "client_host": None,
            "x_forwarded_for": None,
            "x_real_ip": None,
            "detected_real_ip": None,
        }

        response = IPDebugResponse(**valid_data)

        assert response.client_host is None
        assert response.x_forwarded_for is None
        assert response.x_real_ip is None
        assert response.detected_real_ip is None

    def test_valid_ip_debug_response_mixed_values(self):
        """Test valid IPDebugResponse creation with mixed None and string values"""
        valid_data = {
            "client_host": "127.0.0.1",
            "x_forwarded_for": None,
            "x_real_ip": "10.0.0.1",
            "detected_real_ip": "10.0.0.1",
        }

        response = IPDebugResponse(**valid_data)

        assert response.client_host == "127.0.0.1"
        assert response.x_forwarded_for is None
        assert response.x_real_ip == "10.0.0.1"
        assert response.detected_real_ip == "10.0.0.1"

    def test_ip_debug_response_missing_required_fields(self):
        """Test IPDebugResponse validation with missing required fields"""
        # Missing all fields
        with pytest.raises(ValidationError) as exc_info:
            IPDebugResponse()

        errors = exc_info.value.errors()
        assert len(errors) == 4  # All four fields are required

        # Missing some fields
        incomplete_data = {
            "client_host": "192.168.1.1",
            # Missing x_forwarded_for, x_real_ip, detected_real_ip
        }

        with pytest.raises(ValidationError) as exc_info:
            IPDebugResponse(**incomplete_data)

        errors = exc_info.value.errors()
        assert len(errors) == 3  # Three missing fields

    def test_ip_debug_response_invalid_field_types(self):
        """Test IPDebugResponse validation with invalid field types"""
        # Test with non-string values
        invalid_data = {
            "client_host": 123,  # Should be string
            "x_forwarded_for": True,  # Should be string
            "x_real_ip": ["192.168.1.1"],  # Should be string
            "detected_real_ip": 456,  # Should be string
        }

        with pytest.raises(ValidationError) as exc_info:
            IPDebugResponse(**invalid_data)

        errors = exc_info.value.errors()
        assert len(errors) == 4  # All fields have type errors


class TestClearBlockedIPsResponse:
    """Test ClearBlockedIPsResponse schema validation"""

    def test_valid_clear_blocked_ips_response_with_ips(self):
        """Test valid ClearBlockedIPsResponse creation with IPs"""
        valid_data = {
            "cleared_ips": ["192.168.1.1", "10.0.0.1", "203.0.113.1"],
            "count": 3,
        }

        response = ClearBlockedIPsResponse(**valid_data)

        assert response.cleared_ips == ["192.168.1.1", "10.0.0.1", "203.0.113.1"]
        assert response.count == 3
        assert len(response.cleared_ips) == response.count

    def test_valid_clear_blocked_ips_response_empty_list(self):
        """Test valid ClearBlockedIPsResponse creation with empty list"""
        valid_data = {
            "cleared_ips": [],
            "count": 0,
        }

        response = ClearBlockedIPsResponse(**valid_data)

        assert response.cleared_ips == []
        assert response.count == 0
        assert len(response.cleared_ips) == response.count

    def test_valid_clear_blocked_ips_response_single_ip(self):
        """Test valid ClearBlockedIPsResponse creation with single IP"""
        valid_data = {
            "cleared_ips": ["192.168.1.1"],
            "count": 1,
        }

        response = ClearBlockedIPsResponse(**valid_data)

        assert response.cleared_ips == ["192.168.1.1"]
        assert response.count == 1

    def test_clear_blocked_ips_response_missing_required_fields(self):
        """Test ClearBlockedIPsResponse validation with missing required fields"""
        # Missing all fields
        with pytest.raises(ValidationError) as exc_info:
            ClearBlockedIPsResponse()

        errors = exc_info.value.errors()
        assert len(errors) == 2  # Both fields are required

        # Missing count field
        with pytest.raises(ValidationError) as exc_info:
            ClearBlockedIPsResponse(cleared_ips=["192.168.1.1"])

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "count" in str(errors[0])

        # Missing cleared_ips field
        with pytest.raises(ValidationError) as exc_info:
            ClearBlockedIPsResponse(count=1)

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "cleared_ips" in str(errors[0])

    def test_clear_blocked_ips_response_invalid_field_types(self):
        """Test ClearBlockedIPsResponse validation with invalid field types"""
        # Test with invalid cleared_ips type
        with pytest.raises(ValidationError) as exc_info:
            ClearBlockedIPsResponse(cleared_ips="not_a_list", count=1)

        errors = exc_info.value.errors()
        assert any("list_type" in str(error) for error in errors)

        # Test with invalid count type
        with pytest.raises(ValidationError) as exc_info:
            ClearBlockedIPsResponse(cleared_ips=["192.168.1.1"], count="not_an_int")

        errors = exc_info.value.errors()
        assert any("int_parsing" in str(error) for error in errors)

    def test_clear_blocked_ips_response_count_mismatch(self):
        """Test ClearBlockedIPsResponse with count not matching list length"""
        # This should still be valid as count is just a field, not validated against list length
        valid_data = {
            "cleared_ips": ["192.168.1.1", "10.0.0.1"],
            "count": 5,  # Different from actual list length
        }

        response = ClearBlockedIPsResponse(**valid_data)
        assert response.cleared_ips == ["192.168.1.1", "10.0.0.1"]
        assert response.count == 5


class TestSchemaIntegration:
    """Test schema integration and edge cases"""

    def test_schema_field_descriptions(self):
        """Test that schema fields have proper descriptions"""
        # Check IPDebugResponse field descriptions
        ip_debug_fields = IPDebugResponse.model_fields

        assert ip_debug_fields["client_host"].description is not None
        assert ip_debug_fields["x_forwarded_for"].description is not None
        assert ip_debug_fields["x_real_ip"].description is not None
        assert ip_debug_fields["detected_real_ip"].description is not None

        # Check ClearBlockedIPsResponse field descriptions
        clear_blocked_fields = ClearBlockedIPsResponse.model_fields

        assert clear_blocked_fields["cleared_ips"].description is not None
        assert clear_blocked_fields["count"].description is not None

    def test_schema_model_dump(self):
        """Test schema model_dump functionality"""
        # Test IPDebugResponse model_dump
        ip_data = {
            "client_host": "192.168.1.1",
            "x_forwarded_for": "203.0.113.1",
            "x_real_ip": "203.0.113.1",
            "detected_real_ip": "203.0.113.1",
        }
        ip_response = IPDebugResponse(**ip_data)
        dumped = ip_response.model_dump()

        assert dumped == ip_data

        # Test ClearBlockedIPsResponse model_dump
        clear_data = {
            "cleared_ips": ["192.168.1.1", "10.0.0.1"],
            "count": 2,
        }
        clear_response = ClearBlockedIPsResponse(**clear_data)
        dumped = clear_response.model_dump()

        assert dumped == clear_data

    def test_schema_validation_error_details(self):
        """Test that validation errors provide detailed information"""
        with pytest.raises(ValidationError) as exc_info:
            IPDebugResponse(
                client_host=123,  # Wrong type
                x_forwarded_for="valid_string",
                x_real_ip=None,
                detected_real_ip=None,
            )

        errors = exc_info.value.errors()
        error_types = [error["type"] for error in errors]

        # Should have type validation error
        assert len(errors) >= 1
        assert "int_parsing" in error_types or "string_type" in error_types

    def test_schema_with_unicode_values(self):
        """Test schema handling of unicode values in IP fields"""
        # IP addresses should not contain unicode, but test edge case
        unicode_data = {
            "client_host": "192.168.1.1",
            "x_forwarded_for": "203.0.113.1",
            "x_real_ip": "203.0.113.1",
            "detected_real_ip": "203.0.113.1",
        }

        response = IPDebugResponse(**unicode_data)
        assert response.client_host == "192.168.1.1"
        assert response.x_forwarded_for == "203.0.113.1"
        assert response.x_real_ip == "203.0.113.1"
        assert response.detected_real_ip == "203.0.113.1"

    def test_clear_blocked_ips_response_with_large_dataset(self):
        """Test ClearBlockedIPsResponse with large number of IPs"""
        large_ip_list = [f"192.168.1.{i}" for i in range(1000)]
        large_data = {
            "cleared_ips": large_ip_list,
            "count": 1000,
        }

        response = ClearBlockedIPsResponse(**large_data)
        assert len(response.cleared_ips) == 1000
        assert response.count == 1000
        assert response.cleared_ips[0] == "192.168.1.0"
        assert response.cleared_ips[-1] == "192.168.1.999"