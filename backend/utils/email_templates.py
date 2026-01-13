"""
Email templates for the application.
Supports variable substitution using Python string formatting.
Supports both plain text and HTML formats with modern design.
"""
from typing import Dict, Any, Optional
from core.config import settings


class EmailTemplate:
    """Email template with subject, plain text body, and optional HTML body"""
    
    def __init__(
        self, 
        subject: str, 
        body: str, 
        html_body: Optional[str] = None
    ):
        self.subject = subject
        self.body = body
        self.html_body = html_body
    
    def render(self, **kwargs: Any) -> Dict[str, str]:
        """
        Render template with variables.
        
        Args:
            **kwargs: Variables to substitute in template
            
        Returns:
            Dict with 'subject', 'body', and optionally 'html_body' keys
        """
        result = {
            "subject": self.subject.format(**kwargs),
            "body": self.body.format(**kwargs),
        }
        
        if self.html_body:
            result["html_body"] = self.html_body.format(**kwargs)
        
        return result


# Password Reset Email Template
PASSWORD_RESET_TEMPLATE = EmailTemplate(
    subject="Reset your password - {app_name}",
    body=(
        "Hi {user_name},\n\n"
        "You requested a password reset for your {app_name} account.\n\n"
        "Please click the link below to set a new password:\n{reset_url}\n\n"
        "This link will expire in 30 minutes.\n\n"
        "If you did not request this, you can safely ignore this email."
    ),
    html_body=(
        "<!DOCTYPE html>"
        "<html>"
        "<head>"
            "<meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width, initial-scale=1.0'>"
        "</head>"
        "<body style='margin: 0; padding: 20px; font-family: -apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, \"Helvetica Neue\", Arial, sans-serif; background-color: #ffffff;'>"
            "<div style='max-width: 80dvw; margin: 0 auto;'>"
                "<h3 style='margin: 0 0 16px; color: #212529; line-height: 1.6;  font-weight: 500;'>Hi {user_name},</h3>"
                "<p style='margin: 0 0 20px; color: #212529; font-size: 16px; line-height: 1.6;'>"
                    "You requested a password reset for your <strong>{app_name}</strong> account. <br>Click the button below to set a new password. This link will expire in <strong>30 minutes</strong>."
                "</p>"
                "<p style='margin:0 0 28px; user-select: none;'>"
                    "<a href='{reset_url}' "
                        "style='display: inline-block; background-color: #212529; "
                        "color: #ffffff; text-decoration: none; padding: 10px 16px; border-radius: 12px; "
                        "font-size: 16px; font-weight: 500;'"
                    ">"
                        "Reset Password"
                    "</a>"
                "</p>"
                "<p style='width: fit-content; margin: 0; padding: 10px 18px; border-radius: 12px; border: 1px solid #e9ecef; background-color: #f8f9fa; color: #495057; font-size: 14px; line-height: 1.6;'>"
                    "If you did not request this password reset, you can safely ignore this email. Your account remains secure."
                "</p>"
            "</div>"
        "</body>"
        "</html>"
    ),
)
