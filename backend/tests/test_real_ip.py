import pytest
from fastapi import Request
from unittest.mock import Mock
from starlette.datastructures import Address, Headers

from middleware.real_ip import get_real_ip

class TestGetRealIP:
    """Tests for get_real_ip function"""
    
    def create_mock_request(self, headers=None, client_host="127.0.0.1"):
        """Create mock Request object"""
        request = Mock(spec=Request)
        request.headers = Headers(headers or {})
        request.client = Address(client_host, 8000) if client_host else None
        return request
    
    def test_get_real_ip_from_x_forwarded_for(self):
        """Test getting IP from X-Forwarded-For header"""
        request = self.create_mock_request({
            "x-forwarded-for": "192.168.1.100, 10.0.0.1, 172.16.0.1"
        })
        
        result = get_real_ip(request)
        assert result == "192.168.1.100"
    
    def test_get_real_ip_from_x_real_ip(self):
        """Test getting IP from X-Real-IP header"""
        request = self.create_mock_request({
            "x-real-ip": "203.0.113.45"
        })
        
        result = get_real_ip(request)
        assert result == "203.0.113.45"
    
    def test_get_real_ip_priority_forwarded_for_over_real_ip(self):
        """Test X-Forwarded-For priority over X-Real-IP"""
        request = self.create_mock_request({
            "x-forwarded-for": "192.168.1.100",
            "x-real-ip": "203.0.113.45"
        })
        
        result = get_real_ip(request)
        assert result == "192.168.1.100"
    
    def test_get_real_ip_fallback_to_client_host(self):
        """Test fallback to client.host"""
        request = self.create_mock_request({}, client_host="127.0.0.1")
        
        result = get_real_ip(request)
        assert result == "127.0.0.1"
    
    def test_get_real_ip_no_client(self):
        """Test case with no client information"""
        request = self.create_mock_request({}, client_host=None)
        
        result = get_real_ip(request)
        assert result == "unknown"
    
    def test_get_real_ip_strip_whitespace(self):
        """Test whitespace handling in IP strings"""
        request = self.create_mock_request({
            "x-forwarded-for": "  192.168.1.100  , 10.0.0.1"
        })
        
        result = get_real_ip(request)
        assert result == "192.168.1.100"


if __name__ == "__main__":
    # Simple manual testing
    print("Running real_ip module tests...")
    
    test_instance = TestGetRealIP()
    
    try:
        test_instance.test_get_real_ip_from_x_forwarded_for()
        print("✓ X-Forwarded-For test passed")
        
        test_instance.test_get_real_ip_from_x_real_ip()
        print("✓ X-Real-IP test passed")
        
        test_instance.test_get_real_ip_priority_forwarded_for_over_real_ip()
        print("✓ Priority test passed")
        
        test_instance.test_get_real_ip_fallback_to_client_host()
        print("✓ Fallback test passed")
        
        test_instance.test_get_real_ip_no_client()
        print("✓ No client test passed")
        
        test_instance.test_get_real_ip_strip_whitespace()
        print("✓ Whitespace handling test passed")
        
        print("\nAll tests passed! ✨")
        
    except Exception as e:
        print(f"❌ Test failed: {e}") 