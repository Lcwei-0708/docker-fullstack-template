from unittest.mock import MagicMock

from utils.get_real_ip import get_real_ip


class TestGetRealIp:
    def test_prefers_x_real_ip(self):
        request = MagicMock()
        request.headers.get.return_value = "203.0.113.10"
        request.client.host = "10.0.0.1"

        assert get_real_ip(request) == "203.0.113.10"
        request.headers.get.assert_called_once_with("x-real-ip")

    def test_strips_x_real_ip(self):
        request = MagicMock()
        request.headers.get.return_value = "  203.0.113.10  "
        request.client.host = "10.0.0.1"

        assert get_real_ip(request) == "203.0.113.10"

    def test_falls_back_to_client_host(self):
        request = MagicMock()
        request.headers.get.return_value = None
        request.client.host = "10.0.0.1"

        assert get_real_ip(request) == "10.0.0.1"

    def test_returns_unknown_without_client(self):
        request = MagicMock()
        request.headers.get.return_value = None
        request.client = None

        assert get_real_ip(request) == "unknown"
