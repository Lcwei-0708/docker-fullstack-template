import ssl
import smtplib
import logging
from fastapi import FastAPI
from core.config import settings
from dataclasses import dataclass
from email.mime.text import MIMEText
from typing import Iterable, Optional
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from utils.custom_exception import SMTPNotConfiguredException

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SMTPSettings:
    enabled: bool
    host: str
    port: int
    username: Optional[str]
    password: Optional[str]
    from_email: Optional[str]
    from_name: str
    encryption: str


class SMTPMailer:
    def __init__(self, cfg: SMTPSettings):
        self._cfg = cfg

    @property
    def enabled(self) -> bool:
        return self._cfg.enabled

    def _validate(self) -> None:
        if not self._cfg.enabled:
            raise SMTPNotConfiguredException("SMTP is disabled")
        missing = []
        if not self._cfg.host:
            missing.append("SMTP_HOST")
        if not self._cfg.port:
            missing.append("SMTP_PORT")
        if not self._cfg.username:
            missing.append("SMTP_USERNAME/SMTP_USER")
        if not self._cfg.password:
            missing.append("SMTP_PASSWORD")
        if not self._cfg.from_email:
            missing.append("SMTP_FROM_EMAIL/SMTP_FROM")
        if missing:
            raise SMTPNotConfiguredException(f"Missing SMTP settings: {', '.join(missing)}")

        enc = (self._cfg.encryption or "").strip().lower()
        if enc not in {"tls", "ssl", "none"}:
            raise SMTPNotConfiguredException("SMTP_ENCRYPTION must be tls, ssl, or none")

    def _open(self, timeout: int = 30) -> smtplib.SMTP:
        """
        Create a new SMTP connection per send.
        This avoids keeping long-lived connections in the web process.
        """
        self._validate()

        enc = self._cfg.encryption.strip().lower()
        context = ssl.create_default_context()

        if enc == "ssl":
            client: smtplib.SMTP = smtplib.SMTP_SSL(self._cfg.host, self._cfg.port, timeout=timeout, context=context)
        else:
            client = smtplib.SMTP(self._cfg.host, self._cfg.port, timeout=timeout)

        try:
            client.ehlo()
            if enc == "tls":
                client.starttls(context=context)
                client.ehlo()
            if self._cfg.username and self._cfg.password:
                client.login(self._cfg.username, self._cfg.password)
            return client
        except Exception:
            try:
                client.quit()
            except Exception:
                pass
            raise

    def send_text(
        self,
        *,
        to_emails: Iterable[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        timeout: int = 30,
    ) -> None:
        self._validate()

        sender_email = from_email or self._cfg.from_email
        sender_name = from_name or self._cfg.from_name

        # If HTML body is provided, create multipart message
        if html_body:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{sender_name} <{sender_email}>"
            msg["To"] = ", ".join(list(to_emails))
            
            # Add plain text and HTML parts
            part1 = MIMEText(body, "plain", "utf-8")
            part2 = MIMEText(html_body, "html", "utf-8")
            msg.attach(part1)
            msg.attach(part2)
        else:
            # Plain text only
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = f"{sender_name} <{sender_email}>"
            msg["To"] = ", ".join(list(to_emails))
            msg.set_content(body)

        with self._open(timeout=timeout) as client:
            client.send_message(msg)


def build_smtp_settings() -> SMTPSettings:
    return SMTPSettings(
        enabled=bool(settings.SMTP_ENABLE),
        host=(settings.SMTP_HOST or "").strip(),
        port=int(settings.SMTP_PORT),
        username=(settings.SMTP_USERNAME or None),
        password=(settings.SMTP_PASSWORD or None),
        from_email=(settings.SMTP_FROM_EMAIL or None),
        from_name=(settings.SMTP_FROM_NAME or "Docker Fullstack Template"),
        encryption=(settings.SMTP_ENCRYPTION or "tls"),
    )


# Global singleton instance
_SMTP_MAILER: Optional[SMTPMailer] = None


def get_mailer() -> SMTPMailer:
    """
    Get SMTP mailer singleton instance.
    Lazy initialization on first access.
    """
    global _SMTP_MAILER
    if _SMTP_MAILER is None:
        cfg = build_smtp_settings()
        _SMTP_MAILER = SMTPMailer(cfg)
        
        if cfg.enabled:
            logger.info(
                "SMTP enabled: host=%s port=%s encryption=%s from=%s",
                cfg.host,
                cfg.port,
                (cfg.encryption or "").lower(),
                cfg.from_email,
            )
        else:
            logger.info("SMTP disabled")
    
    return _SMTP_MAILER


def add_smtp(app: FastAPI) -> None:
    """
    Initialize SMTP mailer and register to app.state.
    """
    mailer = get_mailer()
    app.state.smtp = mailer