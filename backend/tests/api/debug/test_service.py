import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import Request
from api.debug.services import get_ip_debug_info, clear_blocked_ips
from utils.custom_exception import ServerException
from api.debug.schema import IPDebugResponse, ClearBlockedIPsResponse


class TestGetIPDebugInfo:
    """Test get_ip_debug_info service function"""

    @pytest.mark.asyncio
    async def test_get_ip_debug_info_success_with_all_headers(self):
        """Test successful IP debug info retrieval with all headers present"""
        # Mock request object
        mock_request = MagicMock(spec=Request)
        mock_request.client.host = "192.168.1.1"
        mock_request.headers = {
            "x-forwarded-for": "203.0.113.1, 70.41.3.18, 150.172.238.178",
            "x-real-ip": "203.0.113.1",
        }

        # Mock get_real_ip function
        with patch("api.debug.services.get_real_ip", return_value="203.0.113.1"):
            result = await get_ip_debug_info(mock_request)

        assert isinstance(result, IPDebugResponse)
        assert result.client_host == "192.168.1.1"
        assert result.x_forwarded_for == "203.0.113.1, 70.41.3.18, 150.172.238.178"
        assert result.x_real_ip == "203.0.113.1"
        assert result.detected_real_ip == "203.0.113.1"

    @pytest.mark.asyncio
    async def test_get_ip_debug_info_success_with_no_headers(self):
        """Test successful IP debug info retrieval with no proxy headers"""
        # Mock request object
        mock_request = MagicMock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {}

        # Mock get_real_ip function
        with patch("api.debug.services.get_real_ip", return_value="127.0.0.1"):
            result = await get_ip_debug_info(mock_request)

        assert isinstance(result, IPDebugResponse)
        assert result.client_host == "127.0.0.1"
        assert result.x_forwarded_for is None
        assert result.x_real_ip is None
        assert result.detected_real_ip == "127.0.0.1"

    @pytest.mark.asyncio
    async def test_get_ip_debug_info_success_with_none_client(self):
        """Test successful IP debug info retrieval when client is None"""
        # Mock request object with None client
        mock_request = MagicMock(spec=Request)
        mock_request.client = None
        mock_request.headers = {
            "x-forwarded-for": "203.0.113.1",
            "x-real-ip": "203.0.113.1",
        }

        # Mock get_real_ip function
        with patch("api.debug.services.get_real_ip", return_value="203.0.113.1"):
            result = await get_ip_debug_info(mock_request)

        assert isinstance(result, IPDebugResponse)
        assert result.client_host is None
        assert result.x_forwarded_for == "203.0.113.1"
        assert result.x_real_ip == "203.0.113.1"
        assert result.detected_real_ip == "203.0.113.1"

    @pytest.mark.asyncio
    async def test_get_ip_debug_info_success_partial_headers(self):
        """Test successful IP debug info retrieval with partial headers"""
        # Mock request object
        mock_request = MagicMock(spec=Request)
        mock_request.client.host = "10.0.0.1"
        mock_request.headers = {
            "x-forwarded-for": "203.0.113.1",
            # Missing x-real-ip
        }

        # Mock get_real_ip function
        with patch("api.debug.services.get_real_ip", return_value="203.0.113.1"):
            result = await get_ip_debug_info(mock_request)

        assert isinstance(result, IPDebugResponse)
        assert result.client_host == "10.0.0.1"
        assert result.x_forwarded_for == "203.0.113.1"
        assert result.x_real_ip is None
        assert result.detected_real_ip == "203.0.113.1"

    @pytest.mark.asyncio
    async def test_get_ip_debug_info_exception_handling(self):
        """Test get_ip_debug_info handles exceptions properly"""
        # Mock request object that raises exception
        mock_request = MagicMock(spec=Request)
        mock_request.client.host = "192.168.1.1"
        # Create a mock headers object that can have side_effect
        mock_headers = MagicMock()
        mock_headers.get.side_effect = Exception("Header access error")
        mock_request.headers = mock_headers

        with pytest.raises(ServerException, match="Failed to get IP debug info"):
            await get_ip_debug_info(mock_request)

    @pytest.mark.asyncio
    async def test_get_ip_debug_info_get_real_ip_exception(self):
        """Test get_ip_debug_info handles get_real_ip exceptions"""
        # Mock request object
        mock_request = MagicMock(spec=Request)
        mock_request.client.host = "192.168.1.1"
        mock_request.headers = {}

        # Mock get_real_ip to raise exception
        with patch("api.debug.services.get_real_ip", side_effect=Exception("IP detection error")):
            with pytest.raises(ServerException, match="Failed to get IP debug info"):
                await get_ip_debug_info(mock_request)


class TestClearBlockedIPs:
    """Test clear_blocked_ips service function"""

    @pytest.mark.asyncio
    async def test_clear_blocked_ips_success_with_ips(self):
        """Test successful clearing of blocked IPs"""
        # Mock Redis client
        mock_redis = AsyncMock()
        mock_redis.keys.return_value = ["block:192.168.1.1", "block:10.0.0.1", "block:203.0.113.1"]
        mock_redis.delete.return_value = 1

        # Mock aioredis.from_url as an async function that returns our mock redis
        async def mock_from_url(*args, **kwargs):
            return mock_redis

        with patch("api.debug.services.aioredis.from_url", side_effect=mock_from_url):
            result = await clear_blocked_ips()

        assert isinstance(result, ClearBlockedIPsResponse)
        assert result.cleared_ips == ["192.168.1.1", "10.0.0.1", "203.0.113.1"]
        assert result.count == 3

        # Verify Redis methods were called correctly
        mock_redis.keys.assert_called_once_with("block:*")
        assert mock_redis.delete.call_count == 3

    @pytest.mark.asyncio
    async def test_clear_blocked_ips_success_no_ips(self):
        """Test clearing blocked IPs when no IPs are blocked"""
        # Mock Redis client
        mock_redis = AsyncMock()
        mock_redis.keys.return_value = []

        # Mock aioredis.from_url as an async function that returns our mock redis
        async def mock_from_url(*args, **kwargs):
            return mock_redis

        with patch("api.debug.services.aioredis.from_url", side_effect=mock_from_url):
            result = await clear_blocked_ips()

        assert isinstance(result, ClearBlockedIPsResponse)
        assert result.cleared_ips == []
        assert result.count == 0

        # Verify Redis methods were called correctly
        mock_redis.keys.assert_called_once_with("block:*")
        mock_redis.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_clear_blocked_ips_success_single_ip(self):
        """Test clearing blocked IPs with single IP"""
        # Mock Redis client
        mock_redis = AsyncMock()
        mock_redis.keys.return_value = ["block:192.168.1.1"]
        mock_redis.delete.return_value = 1

        # Mock aioredis.from_url as an async function that returns our mock redis
        async def mock_from_url(*args, **kwargs):
            return mock_redis

        with patch("api.debug.services.aioredis.from_url", side_effect=mock_from_url):
            result = await clear_blocked_ips()

        assert isinstance(result, ClearBlockedIPsResponse)
        assert result.cleared_ips == ["192.168.1.1"]
        assert result.count == 1

    @pytest.mark.asyncio
    async def test_clear_blocked_ips_redis_connection_error(self):
        """Test clear_blocked_ips handles Redis connection errors"""
        with patch("api.debug.services.aioredis.from_url", side_effect=Exception("Redis connection error")):
            with pytest.raises(ServerException, match="Failed to clear blocked IPs"):
                await clear_blocked_ips()

    @pytest.mark.asyncio
    async def test_clear_blocked_ips_keys_error(self):
        """Test clear_blocked_ips handles Redis keys command errors"""
        # Mock Redis client
        mock_redis = AsyncMock()
        mock_redis.keys.side_effect = Exception("Keys command error")

        # Mock aioredis.from_url as an async function that returns our mock redis
        async def mock_from_url(*args, **kwargs):
            return mock_redis

        with patch("api.debug.services.aioredis.from_url", side_effect=mock_from_url):
            with pytest.raises(ServerException, match="Failed to clear blocked IPs"):
                await clear_blocked_ips()

    @pytest.mark.asyncio
    async def test_clear_blocked_ips_delete_error(self):
        """Test clear_blocked_ips handles Redis delete command errors"""
        # Mock Redis client
        mock_redis = AsyncMock()
        mock_redis.keys.return_value = ["block:192.168.1.1"]
        mock_redis.delete.side_effect = Exception("Delete command error")

        # Mock aioredis.from_url as an async function that returns our mock redis
        async def mock_from_url(*args, **kwargs):
            return mock_redis

        with patch("api.debug.services.aioredis.from_url", side_effect=mock_from_url):
            with pytest.raises(ServerException, match="Failed to clear blocked IPs"):
                await clear_blocked_ips()

    @pytest.mark.asyncio
    async def test_clear_blocked_ips_with_mixed_key_formats(self):
        """Test clear_blocked_ips with various key formats"""
        # Mock Redis client
        mock_redis = AsyncMock()
        mock_redis.keys.return_value = [
            "block:192.168.1.1",
            "block:10.0.0.1",
            "block:203.0.113.1",
            "block:invalid-format",
            "block:",
        ]
        mock_redis.delete.return_value = 1

        # Mock aioredis.from_url as an async function that returns our mock redis
        async def mock_from_url(*args, **kwargs):
            return mock_redis

        with patch("api.debug.services.aioredis.from_url", side_effect=mock_from_url):
            result = await clear_blocked_ips()

        assert isinstance(result, ClearBlockedIPsResponse)
        assert result.cleared_ips == ["192.168.1.1", "10.0.0.1", "203.0.113.1", "invalid-format", ""]
        assert result.count == 5

    @pytest.mark.asyncio
    async def test_clear_blocked_ips_redis_url_configuration(self):
        """Test clear_blocked_ips uses correct Redis URL configuration"""
        # Mock Redis client
        mock_redis = AsyncMock()
        mock_redis.keys.return_value = []
        mock_redis.delete.return_value = 1

        # Mock aioredis.from_url as an async function that returns our mock redis
        async def mock_from_url(*args, **kwargs):
            return mock_redis

        with patch("api.debug.services.aioredis.from_url", side_effect=mock_from_url) as mock_from_url_patch:
            await clear_blocked_ips()

            # Verify aioredis.from_url was called with correct parameters
            mock_from_url_patch.assert_called_once()
            call_args = mock_from_url_patch.call_args
            assert "encoding" in call_args.kwargs
            assert "decode_responses" in call_args.kwargs
            assert call_args.kwargs["encoding"] == "utf-8"
            assert call_args.kwargs["decode_responses"] is True


class TestServiceIntegration:
    """Test service layer integration scenarios"""

    @pytest.mark.asyncio
    async def test_get_ip_debug_info_with_real_request_attributes(self):
        """Test get_ip_debug_info with realistic request attributes"""
        # Mock request object with realistic attributes
        mock_request = MagicMock(spec=Request)
        mock_request.client.host = "172.16.0.1"
        mock_request.headers = {
            "x-forwarded-for": "203.0.113.1, 70.41.3.18, 150.172.238.178",
            "x-real-ip": "203.0.113.1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "accept": "application/json",
        }

        # Mock get_real_ip function
        with patch("api.debug.services.get_real_ip", return_value="203.0.113.1"):
            result = await get_ip_debug_info(mock_request)

        assert isinstance(result, IPDebugResponse)
        assert result.client_host == "172.16.0.1"
        assert result.x_forwarded_for == "203.0.113.1, 70.41.3.18, 150.172.238.178"
        assert result.x_real_ip == "203.0.113.1"
        assert result.detected_real_ip == "203.0.113.1"

    @pytest.mark.asyncio
    async def test_clear_blocked_ips_with_large_dataset(self):
        """Test clear_blocked_ips with large number of blocked IPs"""
        # Mock Redis client
        mock_redis = AsyncMock()
        large_key_list = [f"block:192.168.1.{i}" for i in range(100)]
        mock_redis.keys.return_value = large_key_list
        mock_redis.delete.return_value = 1

        # Mock aioredis.from_url as an async function that returns our mock redis
        async def mock_from_url(*args, **kwargs):
            return mock_redis

        with patch("api.debug.services.aioredis.from_url", side_effect=mock_from_url):
            result = await clear_blocked_ips()

        assert isinstance(result, ClearBlockedIPsResponse)
        assert len(result.cleared_ips) == 100
        assert result.count == 100
        assert mock_redis.delete.call_count == 100

    @pytest.mark.asyncio
    async def test_service_error_propagation(self):
        """Test that service errors are properly propagated"""
        # Test get_ip_debug_info error propagation
        mock_request = MagicMock(spec=Request)
        mock_request.client.host = "192.168.1.1"
        # Create a mock headers object that can have side_effect
        mock_headers = MagicMock()
        mock_headers.get.side_effect = Exception("Test error")
        mock_request.headers = mock_headers

        with pytest.raises(ServerException) as exc_info:
            await get_ip_debug_info(mock_request)

        assert "Failed to get IP debug info" in str(exc_info.value)
        assert "Test error" in str(exc_info.value)

        # Test clear_blocked_ips error propagation
        with patch("api.debug.services.aioredis.from_url", side_effect=Exception("Redis error")):
            with pytest.raises(ServerException) as exc_info:
                await clear_blocked_ips()

            assert "Failed to clear blocked IPs" in str(exc_info.value)
            assert "Redis error" in str(exc_info.value)


class TestServiceEdgeCases:
    """Test service layer edge cases and error scenarios"""

    @pytest.mark.asyncio
    async def test_get_ip_debug_info_with_empty_string_headers(self):
        """Test get_ip_debug_info with empty string headers"""
        # Mock request object
        mock_request = MagicMock(spec=Request)
        mock_request.client.host = "192.168.1.1"
        mock_request.headers = {
            "x-forwarded-for": "",
            "x-real-ip": "",
        }

        # Mock get_real_ip function
        with patch("api.debug.services.get_real_ip", return_value="192.168.1.1"):
            result = await get_ip_debug_info(mock_request)

        assert isinstance(result, IPDebugResponse)
        assert result.client_host == "192.168.1.1"
        assert result.x_forwarded_for == ""
        assert result.x_real_ip == ""
        assert result.detected_real_ip == "192.168.1.1"

    @pytest.mark.asyncio
    async def test_clear_blocked_ips_with_mixed_key_formats(self):
        """Test clear_blocked_ips with various key formats that match block:* pattern"""
        # Mock Redis client
        mock_redis = AsyncMock()
        mock_redis.keys.return_value = [
            "block:192.168.1.1",     # Valid IP
            "block:10.0.0.1",        # Valid IP
            "block:invalid-format",  # Invalid IP format but valid block: prefix
            "block:",                # Empty after prefix
        ]
        mock_redis.delete.return_value = 1

        # Mock aioredis.from_url as an async function that returns our mock redis
        async def mock_from_url(*args, **kwargs):
            return mock_redis

        with patch("api.debug.services.aioredis.from_url", side_effect=mock_from_url):
            result = await clear_blocked_ips()

        # The service processes all keys returned by redis.keys("block:*")
        # and removes the "block:" prefix from each key
        assert isinstance(result, ClearBlockedIPsResponse)
        assert result.cleared_ips == ["192.168.1.1", "10.0.0.1", "invalid-format", ""]
        assert result.count == 4

    @pytest.mark.asyncio
    async def test_get_ip_debug_info_with_unicode_headers(self):
        """Test get_ip_debug_info with unicode characters in headers"""
        # Mock request object
        mock_request = MagicMock(spec=Request)
        mock_request.client.host = "192.168.1.1"
        mock_request.headers = {
            "x-forwarded-for": "203.0.113.1, 70.41.3.18, 150.172.238.178",
            "x-real-ip": "203.0.113.1",
        }

        # Mock get_real_ip function
        with patch("api.debug.services.get_real_ip", return_value="203.0.113.1"):
            result = await get_ip_debug_info(mock_request)

        assert isinstance(result, IPDebugResponse)
        assert result.client_host == "192.168.1.1"
        assert result.x_forwarded_for == "203.0.113.1, 70.41.3.18, 150.172.238.178"
        assert result.x_real_ip == "203.0.113.1"
        assert result.detected_real_ip == "203.0.113.1"