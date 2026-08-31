from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI

import extensions.smtp
from extensions.smtp import (
    SMTPMailer,
    SMTPSettings,
    add_smtp,
    build_smtp_settings,
    get_mailer,
)
from utils.custom_exception import SMTPNotConfiguredException


class TestSMTPSettings:
    """Test SMTPSettings dataclass"""

    def test_smtp_settings_creation(self):
        """Test creating SMTPSettings with all fields"""
        settings = SMTPSettings(
            enabled=True,
            host="smtp.example.com",
            port=587,
            username="user@example.com",
            password="password123",
            from_email="from@example.com",
            from_name="Test App",
            encryption="tls",
        )
        assert settings.enabled is True
        assert settings.host == "smtp.example.com"
        assert settings.port == 587
        assert settings.username == "user@example.com"
        assert settings.password == "password123"
        assert settings.from_email == "from@example.com"
        assert settings.from_name == "Test App"
        assert settings.encryption == "tls"

    def test_smtp_settings_optional_fields(self):
        """Test SMTPSettings with optional None fields"""
        settings = SMTPSettings(
            enabled=False,
            host="",
            port=25,
            username=None,
            password=None,
            from_email=None,
            from_name="App",
            encryption="none",
        )
        assert settings.enabled is False
        assert settings.username is None
        assert settings.password is None
        assert settings.from_email is None


class TestSMTPMailer:
    """Test SMTPMailer class"""

    def test_enabled_property(self):
        """Test enabled property"""
        cfg = SMTPSettings(
            enabled=True,
            host="smtp.example.com",
            port=587,
            username="user",
            password="pass",
            from_email="from@example.com",
            from_name="App",
            encryption="tls",
        )
        mailer = SMTPMailer(cfg)
        assert mailer.enabled is True

        cfg_disabled = SMTPSettings(
            enabled=False,
            host="",
            port=25,
            username=None,
            password=None,
            from_email=None,
            from_name="App",
            encryption="none",
        )
        mailer_disabled = SMTPMailer(cfg_disabled)
        assert mailer_disabled.enabled is False

    def test_validate_disabled(self):
        """Test validation when SMTP is disabled"""
        cfg = SMTPSettings(
            enabled=False,
            host="",
            port=25,
            username=None,
            password=None,
            from_email=None,
            from_name="App",
            encryption="none",
        )
        mailer = SMTPMailer(cfg)

        with pytest.raises(SMTPNotConfiguredException) as exc_info:
            mailer._validate()
        assert "SMTP is disabled" in str(exc_info.value)

    def test_validate_missing_host(self):
        """Test validation when host is missing"""
        cfg = SMTPSettings(
            enabled=True,
            host="",
            port=587,
            username="user",
            password="pass",
            from_email="from@example.com",
            from_name="App",
            encryption="tls",
        )
        mailer = SMTPMailer(cfg)

        with pytest.raises(SMTPNotConfiguredException) as exc_info:
            mailer._validate()
        assert "SMTP_HOST" in str(exc_info.value)

    def test_validate_missing_port(self):
        """Test validation when port is missing"""
        cfg = SMTPSettings(
            enabled=True,
            host="smtp.example.com",
            port=0,
            username="user",
            password="pass",
            from_email="from@example.com",
            from_name="App",
            encryption="tls",
        )
        mailer = SMTPMailer(cfg)

        with pytest.raises(SMTPNotConfiguredException) as exc_info:
            mailer._validate()
        assert "SMTP_PORT" in str(exc_info.value)

    def test_validate_missing_username(self):
        """Test validation when username is missing"""
        cfg = SMTPSettings(
            enabled=True,
            host="smtp.example.com",
            port=587,
            username=None,
            password="pass",
            from_email="from@example.com",
            from_name="App",
            encryption="tls",
        )
        mailer = SMTPMailer(cfg)

        with pytest.raises(SMTPNotConfiguredException) as exc_info:
            mailer._validate()
        assert "SMTP_USERNAME" in str(exc_info.value)

    def test_validate_missing_password(self):
        """Test validation when password is missing"""
        cfg = SMTPSettings(
            enabled=True,
            host="smtp.example.com",
            port=587,
            username="user",
            password=None,
            from_email="from@example.com",
            from_name="App",
            encryption="tls",
        )
        mailer = SMTPMailer(cfg)

        with pytest.raises(SMTPNotConfiguredException) as exc_info:
            mailer._validate()
        assert "SMTP_PASSWORD" in str(exc_info.value)

    def test_validate_missing_from_email(self):
        """Test validation when from_email is missing"""
        cfg = SMTPSettings(
            enabled=True,
            host="smtp.example.com",
            port=587,
            username="user",
            password="pass",
            from_email=None,
            from_name="App",
            encryption="tls",
        )
        mailer = SMTPMailer(cfg)

        with pytest.raises(SMTPNotConfiguredException) as exc_info:
            mailer._validate()
        assert "SMTP_FROM_EMAIL" in str(exc_info.value)

    def test_validate_invalid_encryption(self):
        """Test validation with invalid encryption"""
        cfg = SMTPSettings(
            enabled=True,
            host="smtp.example.com",
            port=587,
            username="user",
            password="pass",
            from_email="from@example.com",
            from_name="App",
            encryption="invalid",
        )
        mailer = SMTPMailer(cfg)

        with pytest.raises(SMTPNotConfiguredException) as exc_info:
            mailer._validate()
        assert "SMTP_ENCRYPTION must be tls, ssl, or none" in str(exc_info.value)

    def test_validate_success(self):
        """Test successful validation"""
        cfg = SMTPSettings(
            enabled=True,
            host="smtp.example.com",
            port=587,
            username="user",
            password="pass",
            from_email="from@example.com",
            from_name="App",
            encryption="tls",
        )
        mailer = SMTPMailer(cfg)
        # Should not raise exception
        mailer._validate()

    @patch("extensions.smtp.smtplib.SMTP")
    @patch("extensions.smtp.ssl.create_default_context")
    def test_open_tls(self, mock_ssl_context, mock_smtp):
        """Test opening SMTP connection with TLS"""
        cfg = SMTPSettings(
            enabled=True,
            host="smtp.example.com",
            port=587,
            username="user",
            password="pass",
            from_email="from@example.com",
            from_name="App",
            encryption="tls",
        )
        mailer = SMTPMailer(cfg)

        mock_client = MagicMock()
        mock_smtp.return_value = mock_client
        mock_ssl_context.return_value = MagicMock()

        client = mailer._open()

        mock_smtp.assert_called_once_with("smtp.example.com", 587, timeout=30)
        mock_client.ehlo.assert_called()
        assert mock_client.ehlo.call_count == 2  # Called before and after starttls
        mock_client.starttls.assert_called_once()
        mock_client.login.assert_called_once_with("user", "pass")
        assert client == mock_client

    @patch("extensions.smtp.smtplib.SMTP_SSL")
    @patch("extensions.smtp.ssl.create_default_context")
    def test_open_ssl(self, mock_ssl_context, mock_smtp_ssl):
        """Test opening SMTP connection with SSL"""
        cfg = SMTPSettings(
            enabled=True,
            host="smtp.example.com",
            port=465,
            username="user",
            password="pass",
            from_email="from@example.com",
            from_name="App",
            encryption="ssl",
        )
        mailer = SMTPMailer(cfg)

        mock_client = MagicMock()
        mock_smtp_ssl.return_value = mock_client
        mock_ssl_context.return_value = MagicMock()

        client = mailer._open()

        mock_smtp_ssl.assert_called_once_with(
            "smtp.example.com", 465, timeout=30, context=mock_ssl_context.return_value
        )
        mock_client.ehlo.assert_called_once()
        mock_client.login.assert_called_once_with("user", "pass")
        assert client == mock_client

    @patch("extensions.smtp.smtplib.SMTP")
    def test_open_none_encryption(self, mock_smtp):
        """Test opening SMTP connection with no encryption"""
        cfg = SMTPSettings(
            enabled=True,
            host="smtp.example.com",
            port=25,
            username="user",
            password="pass",
            from_email="from@example.com",
            from_name="App",
            encryption="none",
        )
        mailer = SMTPMailer(cfg)

        mock_client = MagicMock()
        mock_smtp.return_value = mock_client

        client = mailer._open()

        mock_smtp.assert_called_once_with("smtp.example.com", 25, timeout=30)
        mock_client.ehlo.assert_called_once()
        mock_client.starttls.assert_not_called()
        mock_client.login.assert_called_once_with("user", "pass")
        assert client == mock_client

    def test_open_no_auth_validation_error(self):
        """Test that _open raises error when username/password are missing"""
        cfg = SMTPSettings(
            enabled=True,
            host="smtp.example.com",
            port=25,
            username=None,
            password=None,
            from_email="from@example.com",
            from_name="App",
            encryption="none",
        )
        mailer = SMTPMailer(cfg)

        # _validate() is called in _open(), and it requires username and password
        with pytest.raises(SMTPNotConfiguredException) as exc_info:
            mailer._open()
        assert "SMTP_USERNAME" in str(exc_info.value) or "SMTP_PASSWORD" in str(exc_info.value)

    @patch("extensions.smtp.smtplib.SMTP")
    def test_open_connection_error(self, mock_smtp):
        """Test handling connection errors"""
        cfg = SMTPSettings(
            enabled=True,
            host="smtp.example.com",
            port=587,
            username="user",
            password="pass",
            from_email="from@example.com",
            from_name="App",
            encryption="tls",
        )
        mailer = SMTPMailer(cfg)

        mock_client = MagicMock()
        mock_client.ehlo.side_effect = Exception("Connection failed")
        mock_smtp.return_value = mock_client

        with pytest.raises(Exception) as exc_info:
            mailer._open()
        assert "Connection failed" in str(exc_info.value)
        mock_client.quit.assert_called_once()

    @patch.object(SMTPMailer, "_open")
    def test_send_text_plain(self, mock_open):
        """Test sending plain text email"""
        cfg = SMTPSettings(
            enabled=True,
            host="smtp.example.com",
            port=587,
            username="user",
            password="pass",
            from_email="from@example.com",
            from_name="Test App",
            encryption="tls",
        )
        mailer = SMTPMailer(cfg)

        mock_client = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_client

        mailer.send_text(
            to_emails=["to@example.com"],
            subject="Test Subject",
            body="Test body",
        )

        mock_open.assert_called_once()
        mock_client.send_message.assert_called_once()
        msg = mock_client.send_message.call_args[0][0]
        assert msg["Subject"] == "Test Subject"
        assert msg["From"] == "Test App <from@example.com>"
        assert msg["To"] == "to@example.com"

    @patch.object(SMTPMailer, "_open")
    def test_send_text_html(self, mock_open):
        """Test sending HTML email"""
        cfg = SMTPSettings(
            enabled=True,
            host="smtp.example.com",
            port=587,
            username="user",
            password="pass",
            from_email="from@example.com",
            from_name="Test App",
            encryption="tls",
        )
        mailer = SMTPMailer(cfg)

        mock_client = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_client

        mailer.send_text(
            to_emails=["to1@example.com", "to2@example.com"],
            subject="Test Subject",
            body="Plain text",
            html_body="<html><body>HTML content</body></html>",
        )

        mock_open.assert_called_once()
        mock_client.send_message.assert_called_once()
        msg = mock_client.send_message.call_args[0][0]
        assert msg["Subject"] == "Test Subject"
        assert msg["From"] == "Test App <from@example.com>"
        assert msg["To"] == "to1@example.com, to2@example.com"
        assert msg.is_multipart() is True

    @patch.object(SMTPMailer, "_open")
    def test_send_text_custom_from(self, mock_open):
        """Test sending email with custom from address"""
        cfg = SMTPSettings(
            enabled=True,
            host="smtp.example.com",
            port=587,
            username="user",
            password="pass",
            from_email="default@example.com",
            from_name="Default Name",
            encryption="tls",
        )
        mailer = SMTPMailer(cfg)

        mock_client = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_client

        mailer.send_text(
            to_emails=["to@example.com"],
            subject="Test Subject",
            body="Test body",
            from_email="custom@example.com",
            from_name="Custom Name",
        )

        msg = mock_client.send_message.call_args[0][0]
        assert msg["From"] == "Custom Name <custom@example.com>"

    @patch.object(SMTPMailer, "_open")
    def test_send_text_custom_timeout(self, mock_open):
        """Test sending email with custom timeout"""
        cfg = SMTPSettings(
            enabled=True,
            host="smtp.example.com",
            port=587,
            username="user",
            password="pass",
            from_email="from@example.com",
            from_name="App",
            encryption="tls",
        )
        mailer = SMTPMailer(cfg)

        mock_client = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_client

        mailer.send_text(
            to_emails=["to@example.com"],
            subject="Test Subject",
            body="Test body",
            timeout=60,
        )

        mock_open.assert_called_once_with(timeout=60)


class TestBuildSMTPSettings:
    """Test build_smtp_settings function"""

    @patch("extensions.smtp.settings")
    def test_build_smtp_settings_enabled(self, mock_settings):
        """Test building SMTP settings when enabled"""
        mock_settings.SMTP_ENABLE = True
        mock_settings.SMTP_HOST = "smtp.example.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USERNAME = "user"
        mock_settings.SMTP_PASSWORD = "pass"
        mock_settings.SMTP_FROM_EMAIL = "from@example.com"
        mock_settings.SMTP_FROM_NAME = "Test App"
        mock_settings.SMTP_ENCRYPTION = "tls"

        settings = build_smtp_settings()

        assert settings.enabled is True
        assert settings.host == "smtp.example.com"
        assert settings.port == 587
        assert settings.username == "user"
        assert settings.password == "pass"
        assert settings.from_email == "from@example.com"
        assert settings.from_name == "Test App"
        assert settings.encryption == "tls"

    @patch("extensions.smtp.settings")
    def test_build_smtp_settings_disabled(self, mock_settings):
        """Test building SMTP settings when disabled"""
        mock_settings.SMTP_ENABLE = False
        mock_settings.SMTP_HOST = ""
        mock_settings.SMTP_PORT = 25
        mock_settings.SMTP_USERNAME = None
        mock_settings.SMTP_PASSWORD = None
        mock_settings.SMTP_FROM_EMAIL = None
        mock_settings.SMTP_FROM_NAME = "App"
        mock_settings.SMTP_ENCRYPTION = "none"

        settings = build_smtp_settings()

        assert settings.enabled is False

    @patch("extensions.smtp.settings")
    def test_build_smtp_settings_defaults(self, mock_settings):
        """Test building SMTP settings with default values"""
        mock_settings.SMTP_ENABLE = True
        mock_settings.SMTP_HOST = "  smtp.example.com  "
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USERNAME = "  user  "
        mock_settings.SMTP_PASSWORD = "pass"
        mock_settings.SMTP_FROM_EMAIL = None
        mock_settings.SMTP_FROM_NAME = None
        mock_settings.SMTP_ENCRYPTION = None

        settings = build_smtp_settings()

        assert settings.host == "smtp.example.com"  # Stripped
        assert settings.username == "  user  "  # Not stripped, kept as is
        assert settings.from_email is None
        assert settings.from_name == "Docker Fullstack Template"  # Default
        assert settings.encryption == "tls"  # Default


class TestGetMailer:
    """Test get_mailer function"""

    def setup_method(self):
        """Reset singleton before each test"""
        extensions.smtp._SMTP_MAILER = None

    @patch("extensions.smtp.build_smtp_settings")
    @patch("extensions.smtp.logger")
    def test_get_mailer_first_call(self, mock_logger, mock_build):
        """Test get_mailer on first call creates instance"""
        mock_cfg = SMTPSettings(
            enabled=True,
            host="smtp.example.com",
            port=587,
            username="user",
            password="pass",
            from_email="from@example.com",
            from_name="App",
            encryption="tls",
        )
        mock_build.return_value = mock_cfg

        mailer1 = get_mailer()

        assert mailer1 is not None
        mock_build.assert_called_once()
        mock_logger.info.assert_called_once()

    @patch("extensions.smtp.build_smtp_settings")
    @patch("extensions.smtp.logger")
    def test_get_mailer_singleton(self, mock_logger, mock_build):
        """Test get_mailer returns same instance (singleton)"""
        mock_cfg = SMTPSettings(
            enabled=True,
            host="smtp.example.com",
            port=587,
            username="user",
            password="pass",
            from_email="from@example.com",
            from_name="App",
            encryption="tls",
        )
        mock_build.return_value = mock_cfg

        mailer1 = get_mailer()
        mailer2 = get_mailer()

        assert mailer1 is mailer2
        assert mock_build.call_count == 1  # Only called once

    @patch("extensions.smtp.build_smtp_settings")
    @patch("extensions.smtp.logger")
    def test_get_mailer_disabled_logging(self, mock_logger, mock_build):
        """Test get_mailer logs when SMTP is disabled"""
        mock_cfg = SMTPSettings(
            enabled=False,
            host="",
            port=25,
            username=None,
            password=None,
            from_email=None,
            from_name="App",
            encryption="none",
        )
        mock_build.return_value = mock_cfg

        get_mailer()

        mock_logger.info.assert_called_once_with("SMTP disabled")


class TestAddSMTP:
    """Test add_smtp function"""

    def setup_method(self):
        """Reset singleton before each test"""
        extensions.smtp._SMTP_MAILER = None

    @patch("extensions.smtp.get_mailer")
    def test_add_smtp_registers_to_app(self, mock_get_mailer):
        """Test add_smtp registers mailer to app.state"""
        app = FastAPI()
        mock_mailer = MagicMock()
        mock_get_mailer.return_value = mock_mailer

        add_smtp(app)

        mock_get_mailer.assert_called_once()
        assert app.state.smtp == mock_mailer
